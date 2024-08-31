# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import sys
import traceback
from datetime import datetime
from http import HTTPStatus

from aiohttp import web
from aiohttp.web import Request, Response, json_response
from botbuilder.core import (
    MemoryStorage,
    TurnContext,
    UserState,
    ConversationState
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity, ActivityTypes
from bots import ManufacturingSupportBot
import pyodbc
from cfg import config

CONFIG = config.DefaultConfig()
DB_CONFIG = config.DbConfig()

db_cnxn = pyodbc.connect('DRIVER={' + DB_CONFIG.MSSQL_DRIVER + '};\
                         SERVER=' + DB_CONFIG.MSSQL_HOST + ';\
                         DATABASE=' + DB_CONFIG.MSSQL_DATABASE + ';\
                         UID=' + DB_CONFIG.MSSQL_USERNAME + ';\
                         PWD=' + DB_CONFIG.MSSQL_PASSWORD)

ADAPTER = CloudAdapter(ConfigurationBotFrameworkAuthentication(CONFIG))


# Catch-all for errors.
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
    await context.send_activity(
        "To continue to run this bot, please fix the bot source code."
    )
    # Send a trace activity if we're talking to the Bot Framework Emulator
    if context.activity.channel_id == "emulator":
        # Create a trace activity that contains the error object
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.utcnow(),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
        )
        # Send a trace activity, which will be displayed in Bot Framework Emulator
        await context.send_activity(trace_activity)


ADAPTER.on_turn_error = on_error

# Create MemoryStorage, UserState
MEMORY = MemoryStorage()
USER_STATE = UserState(MEMORY)
CONVERSATION_STATE = ConversationState(MEMORY)

# Create the Bot
BOT = ManufacturingSupportBot(CONVERSATION_STATE,
                              USER_STATE,
                              db_cnxn=db_cnxn)


async def messages(req: Request) -> Response:
    # Main bot message handler.
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return Response(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    response = await ADAPTER.process_activity(auth_header, activity, BOT.on_turn)
    if response:
        return json_response(data=response.body, status=response.status)
    return Response(status=HTTPStatus.OK)


def init_func(argv):
    APP = web.Application(middlewares=[aiohttp_error_middleware])
    APP.router.add_post('api/messages', messages)
    return APP


if __name__ == "__main__":
    APP = init_func(None)
    try:
        web.run_app(APP, host='localhost', port=CONFIG.PORT)
    except Exception as error:
        raise error
