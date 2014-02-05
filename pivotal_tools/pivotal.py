# Core Imports
from __future__ import unicode_literals
import json
import logging
try:
    from urllib.parse import quote as quote
except ImportError:
    from urllib import quote

# 3rd Party Imports
import requests
import dicttoxml


def find_project_for_story(story_id, token):
    """If we have multiple projects, will loop through the projects to
    find the one with the given story.  returns None if not found
    """
    for project in projects(token):
        story = Project(project['id']).load_story(story_id)
        if story is not None:
            return project

    #Not found
    print("No project found for story: #{}".format(story_id))
    return None


def get_project_by_index(index):
    return Project.all()[index]


def story_first_label(story):
    first_label = ''
    if story['labels']:
        first_label = story['labels'][0]['name']
    return first_label


def find_story(story_id, api_token, project_index=None):
    project = None
    projects_ = projects(api_token)
    if project_index is not None:
        projects_ = projects_[project_index]

    for project in projects_:
        stories = (Project(project['id'], api_token)
                   .stories('id:{}'.format(story_id)))
        if stories:
            return stories[0]


def projects(api_token):
    """returns all projects for the given user"""
    return _perform_pivotal_get('/projects', api_token)


class Project(object):
    BUG = 'type:bug'
    FEATURE = 'type:feature'
    UNSCHEDULED = 'unscheduled'
    UNSTARTED = 'unstarted'
    REJECTED = 'rejected'
    STARTED = 'started'
    FINISHED = 'finished'
    DELIVERED = 'delivered'
    ACCEPTED = 'accepted'

    state_flow = [UNSCHEDULED, UNSTARTED, REJECTED, STARTED, FINISHED, DELIVERED, ACCEPTED]

    """object representation of a Pivotal Project"""

    def __init__(self, pid, api_token, workflow_exit=ACCEPTED):
        self.pid = pid
        self.api_token = api_token
        self.workflow_exit = workflow_exit

    def create_story(self,story_dict):
        stories_url = "/projects/{}/stories".format(self.project_id)
        story_xml = dicttoxml.dicttoxml(story_dict, root=False)
        _perform_pivotal_post(stories_url, story_xml)

    def unestimated_stories(self):
        stories = self.get_stories('type:feature state:unstarted')
        return self.open_bugs() + [story for story in stories if int(story.estimate) == -1]

    def stories(self, *filter_strings):
        """
         Given a list of filter string, returns an list of stories matching
         that filter. If none will return an empty list.  Look at
         [link](https://www.pivotaltracker.com/help/faq#howcanasearchberefined)
         for syntax

        """
        story_filter = quote(' '.join(filter_strings)
                             .encode('utf-8'), safe=b'')
        stories = _perform_pivotal_get(
            '/projects/{}/stories?fields=owners,comments(person,:default)'
            ',tasks,:default'
            '&filter={}'.format(
                self.pid, story_filter), self.api_token)
        # Owners does not get expanded properly by the API
        for story in stories:
            if story['owner_ids'] and not story['owners']:
                story['owners'] = self.story_owners(story)
        return stories

    def story_owners(self, story):
        return _perform_pivotal_get(
            '/projects/{}/stories/{}/owners'.format(self.pid, story['id']),
            self.api_token)

    def open_stories(self, owner=None):
        return self.stories(self.filter_open(), self.filter_owner(owner))

    def in_progress_stories(self):
        return self.stories(self.FEATURE, self.filter_in_progress())

    def finished_stories(self):
        return self.stories(self.FEATURE, self.filter_done())

    def open_bugs(self):
        return self.stories(self.BUG, self.filter_open())

    def finished_bugs(self):
        return self.stories(self.BUG, self.filter_done())

    def filter_open(self):
        return 'state:{}'.format(
            ','.join(self.state_flow[:self.state_flow.index(self.workflow_exit)]))

    def filter_in_progress(self):
        return 'state:{}'.format(
            ','.join(
                self.state_flow[
                    self.state_flow.index(self.REJECTED)
                    :self.state_flow.index(self.workflow_exit)]))

    def filter_done(self):
        return 'state:{} includedone:true'.format(
            ','.join(
                self.state_flow[self.state_flow.index(self.workflow_exit):]))

    def filter_owner(self, owner=None):
        if owner is not None:
            return 'owner:{}'.format(owner)
        else:
            return ''


# TODO Handle requests.exceptions.ConnectionError

def _perform_pivotal_get(url, token):
    headers = {'X-TrackerToken': token}
    response = requests.get(
        'https://www.pivotaltracker.com/services/v5' + url, headers=headers)
    logging.debug(response.text)
    return json.loads(response.text)


def _perform_pivotal_put(url):
    headers = {'X-TrackerToken': TOKEN, 'Content-Length': 0}
    response = requests.put(
        'https://www.pivotaltracker.com/services/v5' + url,
        headers=headers)
    response.raise_for_status()
    return response

def _perform_pivotal_post(url,payload_xml):
    headers = {'X-TrackerToken': TOKEN, 'Content-type': "application/xml"}
    response = requests.post(
        'https://www.pivotaltracker.com/services/v5' + url,
        data=payload_xml, headers=headers)
    response.raise_for_status()
    return response
