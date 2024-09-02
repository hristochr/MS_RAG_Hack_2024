import time
import pyodbc
from datetime import datetime
import logging

from botbuilder.core import (
    ActivityHandler,
    TurnContext,
    UserState,
    ConversationState,
    CardFactory,
    MessageFactory,
)
from botbuilder.schema import (
    Activity,
    ActivityTypes,
    Attachment,
    ChannelAccount,
    HeroCard,
    CardImage,
    CardAction,
    ActionTypes,
)

from data_models import (
    # WelcomeUserState,
    UserProfile,
    ConversationData
)
from azr.azropenaisvc import OpenAIServiceResponder


class ManufacturingSupportBot(ActivityHandler):
    def __init__(self,
                 conversation_state: ConversationState,
                 user_state: UserState,
                 db_cnxn: pyodbc.Connection):
        if conversation_state is None:
            raise TypeError(
                "[StateManagementBot]: Missing parameter. conversation_state is required but None was given"
            )

        if user_state is None:
            raise TypeError(
                "[WelcomeUserBot]: Missing parameter. user_state is required but None was given"
            )

        self.conversation_state = conversation_state
        self.user_state = user_state

        self.conversation_data_accessor = self.conversation_state.create_property('ConversationData')
        self.user_profile_accessor = self.user_state.create_property('UserProfile')

        self.db_cnxn = db_cnxn
        # self.user_state_accessor = self.user_state.create_property("WelcomeUserState")

        self.WELCOME_MESSAGE = """This is the CNC Machining Support Chatbot. The bot will first ask you about your name.
                                If you are running this bot in the Bot Framework Emulator, press the
                                'Restart Conversation' button to simulate user joining a bot or a channel.
                                If you are in a web environment refresh the page to start over."""

        self.INFO_MESSAGE = """"""

        self.PATTERN_MESSAGE = """The bot supports the following functionalities:\
            1. Answering questions related to company CNC machinining process, and\
            2. Providing general guidance in case of issues related to production.\
            You can say 'help' or 'intro' to see the introductory help card."""

    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)

        # save changes to WelcomeUserState after each turn
        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    async def on_members_added_activity(self,
                                        members_added: list[ChannelAccount],
                                        turn_context: TurnContext):
        """
        Greet when users are added to the conversation.
        Note that all channels do not send the conversation update activity.
        If you find that this bot works in the emulator, but does not in
        another channel the reason is most likely that the channel does not
        send this activity.
        """
        user_profile = await self.user_profile_accessor.get(turn_context,
                                                            UserProfile)
        conversation_data = await self.conversation_data_accessor.get(turn_context,
                                                                      ConversationData)

        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    f"Hi there { member.name }. " + self.WELCOME_MESSAGE
                )

                # uncomment for an extra message
                # await turn_context.send_activity(self.INFO_MESSAGE)

                await turn_context.send_activity(self.PATTERN_MESSAGE)

                if conversation_data.prompted_for_user_name:
                    # Set the name to what the user provided.
                    user_profile.name = turn_context.activity.text

                    # Acknowledge that we got their name.
                    await turn_context.send_activity(
                        f"Thanks, { user_profile.name }. To continue interacting with the Specdiver bot, type anything."
                    )

                    # Reset the flag to allow the bot to go though the cycle again.
                    conversation_data.prompted_for_user_name = False
                else:
                    # Prompt the user for their name.
                    await turn_context.send_activity("What is your name?")

                    # Set the flag to true, so we don't prompt in the next turn.
                    conversation_data.prompted_for_user_name = True

    async def on_message_activity(self,
                                  turn_context: TurnContext):
        """
        Respond to messages sent from the user.
        """
        user_profile = await self.user_profile_accessor.get(turn_context, UserProfile)
        conversation_data = await self.conversation_data_accessor.get(turn_context, ConversationData)
        current_context = ''
        if user_profile.name is None:
            # First time around this is undefined, so we will prompt user for name.
            if conversation_data.prompted_for_user_name:
                # Set the name to what the user provided.
                user_profile.name = turn_context.activity.text

                # Acknowledge that we got their name.
                await turn_context.send_activity(
                    f"Thanks, { user_profile.name }. To continue interacting with the Specdiver bot, type anything."
                )

                # Reset the flag to allow the bot to go though the cycle again.
                conversation_data.prompted_for_user_name = False
        else:
            if turn_context.activity.text not in ('1', '2', '3', '4', '5'):  # it is not rating

                text = turn_context.activity.text.lower()
                current_context += ' ' + text
                query = [
                    {"role": "system",
                     "content": "You are a manufacturing process expert. Your task is to help junior operators resolve \
                     CNC machining process problems by providing accurate answers based on the data you \
                     have. If the  answer is not available in the retrieved data, reply with \
                     'I do not know. Maybe the answer you are looking for is not part of the source data.'", },
                    {"role": "user",
                     "content": text},
                    {"role": "assistant",
                     "content": current_context}]

                if text in ("hello", "hi"):
                    await turn_context.send_activity(f"You said { text }")
                elif text in ("intro", "help"):
                    await self.__send_intro_card(turn_context)
                else:
                    # typing ...
                    typing_indicator_activity = Activity(type=ActivityTypes.typing)
                    await turn_context.send_activity(typing_indicator_activity)

                    gpt_response = await self.__get_gpt_response(q=query)
                    text_response = gpt_response.text

                    await turn_context.send_activity(MessageFactory.attachment(
                                                        CardFactory.hero_card(gpt_response)))
                    # Display or save state data.
                    conversation_data.timestamp = self.__datetime_from_utc_to_local(
                        turn_context.activity.timestamp
                    )
                    conversation_data.channel_id = turn_context.activity.channel_id
                    conversation_data.gpt_response = text_response
                    conversation_data.interaction_type = 'rag'

                    await self.save_conversation_data(user_profile,
                                                      conversation_data,
                                                      turn_context)

                    # ask for rating
                    await self.prompt_for_rating(turn_context)
            else:  # it is a rating response turn_context.activity.value in ('1','2','3','4','5')
                rating_value = int(turn_context.activity.text)
                # Handle the user's rating, e.g., save it to a database
                conversation_data.timestamp = self.__datetime_from_utc_to_local(
                    turn_context.activity.timestamp
                )
                conversation_data.channel_id = turn_context.activity.channel_id
                conversation_data.gpt_response = rating_value
                conversation_data.interaction_type = 'rating'
                await self.save_to_db(user_profile,
                                      conversation_data,
                                      turn_context)
                await turn_context.send_activity(f"Thank you for rating {rating_value}!")

    async def save_conversation_data(self,
                                     up: UserProfile,
                                     cd: ConversationData,
                                     tc: TurnContext) -> list[Activity] | None:
        """Saves conversation data to the database.

        Args:
            up (UserProfile): current user
            cd (ConversationData): current conversation
            tc (TurnContext): current contenxt

        Returns:
            list[Activity] | None: returns a list of activiites (messages) only if in the "emualtor" channel.
            Otherwise saves to db and returns None
        """
        try:
            await self.save_to_db(up,
                                  cd,
                                  tc)
            # uncomment the check below so that messages will be echoed back in the emulator and saved to db
            # only in case bot is accessed from another channel
            #
            # if tc.activity.channel_id in ('emulator', 'webchat'):
            #     # just echo
            #     return await tc.send_activities([Activity(
            #                                 type=ActivityTypes.message,
            #                                 text=f"{ up.name } sent: { tc.activity.text }."),
            #                             Activity(
            #                                 type=ActivityTypes.message,
            #                                 text=f"{ up.name } received: {cd.gpt_response}."),
            #                             Activity(
            #                                 type=ActivityTypes.message,
            #                                 text=f"Message received at: { cd.timestamp }"),
            #                             Activity(
            #                                 type=ActivityTypes.message,
            #                                 text=f"Message received from: { cd.channel_id }")])
            # else:
            #     # logic to save the data to cosmos db (ideally - but for now to MSSQL)
            #     await self.save_to_db(up,
            #                           cd,
            #                           tc)
        except Exception as e:
            logging.error(f'Error saving chat history: {e}.')

    async def prompt_for_rating(self, turn_context: TurnContext):
        rating_options = [
            CardAction(type=ActionTypes.im_back, title="1", value="1"),
            CardAction(type=ActionTypes.im_back, title="2", value="2"),
            CardAction(type=ActionTypes.im_back, title="3", value="3"),
            CardAction(type=ActionTypes.im_back, title="4", value="4"),
            CardAction(type=ActionTypes.im_back, title="5", value="5")
        ]

        buttons = [CardAction(title=option.title,
                              type=option.type,
                              value=option.value) for option in rating_options]
        card = HeroCard(title='Rate your experience',
                        text='1 being the lowest and 5 the highest rating.',
                        buttons=buttons)
        attachment = Attachment(content_type="application/vnd.microsoft.card.hero",
                                content=card.serialize())

        prompt_message = Activity(
            type=ActivityTypes.message,
            attachments=[attachment]
        )

        await turn_context.send_activity(prompt_message)

    async def save_to_db(self,
                         up: UserProfile,
                         cd: ConversationData,
                         tc: TurnContext) -> None:
        """Saves conversation data to the database.

        Args:
            up (UserProfile): current user
            cd (ConversationData): current conversation
            tc (TurnContext): current contenxt

        Returns:
            None: saves the rating to db.
        """
        try:
            cursor = self.db_cnxn.cursor()
        except Exception as e:
            logging.error(f'Error creating db connection: {e}.')

        try:
            # current state
            rating, prompt = None, None
            try:
                rating = int(tc.activity.text)
            except Exception:
                prompt = tc.activity.text

            user_name = up.name
            response = cd.gpt_response
            channel = cd.channel_id
            interaction_type = cd.interaction_type

            insert_statement = "INSERT INTO Content.AIBotChatHistory (Rating, UserName, Prompt, Response, Channel,\
                InteractionType) VALUES (?, ?, ?, ?, ?, ?)"
            cursor.execute(insert_statement, [rating, user_name, prompt, response, channel, interaction_type])
            cursor.commit()
        except Exception as e:
            logging.error(f'Error saving rating to db: {e}.')

    async def __get_gpt_response(self,
                                 q: list[dict[str:str]]) -> HeroCard:

        gpt = OpenAIServiceResponder()
        try:
            response = await gpt.get_completion(q)
            card = HeroCard(
                title='Answer: ',
                text=response[0],
                buttons=None
            )

            bullet_points = "\n\n".join([f"doc {index}. {title}: {content[:50]}..."
                                         for index, title, content in response[1]])
            card.text += "\n\n" + 'References:' + "\n\n" + bullet_points

            return card

        except Exception as e:
            logging.error(f'Error getting response from the AOAI Service: {e}.')

    async def __send_intro_card(self,
                                turn_context: TurnContext):
        card = HeroCard(
            title="Welcome to the Specdiver AI-powered Bot!",
            text="Ask the bot anything related to SPC0011. If you want to get a summary of something, \
                type 'summarize this text' or 'provide a summary' or 'give me a summary', followed by the text. \
                To see this card again, type 'help' or 'intro.'",
            images=[CardImage(url="https://aka.ms/bf-welcome-card-image")],
            buttons=[
                CardAction(
                    type=ActionTypes.open_url,
                    title="Get an overview",
                    text="Get an overview",
                    display_text="Get an overview",
                    value="https://docs.microsoft.com/en-us/azure/bot-service/?view=azure-bot-service-4.0",
                ),
                CardAction(
                    type=ActionTypes.open_url,
                    title="Ask a question",
                    text="Ask a question",
                    display_text="Ask a question",
                    value="https://stackoverflow.com/questions/tagged/botframework",
                ),
                CardAction(
                    type=ActionTypes.open_url,
                    title="Learn how to deploy",
                    text="Learn how to deploy",
                    display_text="Learn how to deploy",
                    value="https://docs.microsoft.com/en-us/azure/bot-service/bot-builder-howto-deploy-azure?\
                        view=azure-bot-service-4.0",
                ),
            ],
        )

        return await turn_context.send_activity(
            MessageFactory.attachment(CardFactory.hero_card(card))
        )

    def __datetime_from_utc_to_local(self, utc_datetime):
        now_timestamp = time.time()
        offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(
            now_timestamp
        )
        result = utc_datetime + offset
        return result.strftime("%I:%M:%S %p, %A, %B %d of %Y")
