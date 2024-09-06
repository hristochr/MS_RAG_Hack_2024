class ConversationData:
    def __init__(
        self,
        timestamp: str = None,
        channel_id: str = None,
        prompted_for_user_name: bool = False,
        gpt_response: str = None,
        interaction_type: str = None
    ):
        self.timestamp = timestamp
        self.channel_id = channel_id
        self.prompted_for_user_name = prompted_for_user_name
        self.gpt_response = gpt_response
        self.interaction_type = interaction_type