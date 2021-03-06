import argparse
import asyncio
from pprint import pprint
import itertools
import json
import operator

import urwid

from loaf.slack_api import WebClient
from loaf.models import TeamOverview, Team, User
from loaf import ui

loop = asyncio.get_event_loop()


def JSONType(value):
    with open(value, 'r') as fp:
        return json.load(fp)


async def run(config):
    overview = TeamOverview()
    widget = ui.LoafWidget(overview)

    for team_config in config.get('team', []):
        client = WebClient(team_config['token'], loop=loop)

        rtm_client, team_info = await asyncio.gather(
            client.rtm.connect(),
            client.auth.test()
        )
        getter = operator.itemgetter('user_id', 'user', 'team_id', 'team')
        user_id, user, team_id, team = getter(team_info)

        team = Team(
            team_id, team, User(user_id, user),
            web_api=client, rtm_api=rtm_client,
            alias=team_config.get('alias', None)
        )
        await asyncio.gather(team.load_converstions(), team.load_users())

        rtm_client.on('message', team.handle_message)

        overview.add_team(team)

    return widget


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config', '-c',
        metavar='CONFIG',
        default='config.json',
        type=JSONType
    )
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    widget = loop.run_until_complete(run(args.config))

    urwid.MainLoop(widget, [
        ('selected', 'default, standout', 'default'),
        ('username', 'default, bold', 'default')
    ], event_loop=urwid.AsyncioEventLoop(loop=loop)).run()


if __name__ == '__main__':
    main()
