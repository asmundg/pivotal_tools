from __future__ import unicode_literals
import pytest
import vcr

from pivotal_tools import pivotal


@pytest.fixture
def api_token():
    return '36df95a9c01924b348f33b58a2899da8'


@pytest.fixture
def project(api_token):
    return pivotal.Project(1009540, api_token)


def test_projects(api_token):
    with vcr.use_cassette('tests/fixtures/projects.yaml'):
        projects = pivotal.projects(api_token)
        assert len(projects) == 1
        assert len([s for s in projects if s['kind'] == 'project']) == 1


def test_project_open_stories(project):
    with vcr.use_cassette('tests/fixtures/open_stories.yaml'):
        stories = project.open_stories()
        assert (sorted([s['name'] for s in stories])
                == sorted(['unscheduled', 'unstarted', 'started',
                           'finished', 'delivered']))


def test_project_open_stories_owner(project):
    with vcr.use_cassette('tests/fixtures/open_stories_owner.yaml'):
        stories = project.open_stories()
        assert (sorted([s['name'] for s in stories])
                == sorted(['unscheduled', 'unstarted', 'started',
                           'finished', 'delivered']))


def test_project_open_stories_other_owner(project):
    with vcr.use_cassette('tests/fixtures/open_stories_other_owner.yaml'):
        stories = project.open_stories('FOO')
        assert sorted([s['name'] for s in stories]) == []


def test_project_in_progress_stories(project):
    with vcr.use_cassette('tests/fixtures/in_progress_stories.yaml'):
        stories = project.in_progress_stories()
        assert (sorted([s['name'] for s in stories])
                == sorted(['started', 'finished', 'delivered']))


def test_project_finished_stories(project):
    with vcr.use_cassette('tests/fixtures/finished_stories.yaml'):
        stories = project.finished_stories()
        assert (sorted([s['name'] for s in stories])
                == sorted(['accepted']))


def test_open_bugs(project):
    with vcr.use_cassette('tests/fixtures/open_bugs.yaml'):
        stories = project.open_bugs()
        assert (sorted([s['name'] for s in stories])
                == sorted(['unstarted bug', 'started bug', 'finished bug',
                           'delivered bug']))


def test_project_finished_bugs(project):
    with vcr.use_cassette('tests/fixtures/finished_bugs.yaml'):
        stories = project.finished_bugs()
        assert (sorted([s['name'] for s in stories])
                == sorted(['accepted bug']))
