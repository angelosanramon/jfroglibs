import requests
import json
import threading
from . import xray
from concurrent.futures import ThreadPoolExecutor

requests.packages.urllib3.disable_warnings()

class Artifactory:
    '''
    This module provides methods for getting information about a 
    particular Artifactory cluster.
    '''

    def __init__(self, *, url, token, ssl_verify=True, concurrent_workers=20):
        self.url                = url.strip("/")
        self.token              = token
        self._projects          = {}
        self._users             = {}
        self._groups            = {}
        self._repositories      = {}
        self._tokens            = {}
        self._service_accounts  = {}
        self.ssl_verify         = ssl_verify
        self.concurrent_workers = concurrent_workers
        self.session_storage    = threading.local()
        setattr(self.session_storage, 'session', requests.Session())

    @property
    def projects(self):
        if not self._projects:
            self._projects = self._get_all_projects()
        return self._projects
    
    @property
    def users(self):
        if not self._users:
            self._users = self._get_all_users()
        return self._users

    @property
    def groups(self):
        if not self._groups:
            self._groups = self._get_all_groups()
        return self._groups

    @property
    def repositories(self):
        if not self._repositories:
            self._repositories = self._get_all_repositories()
        return self._repositories
    
    @property
    def tokens(self):
        if not self._tokens:
            self._tokens = self._get_all_tokens()
        return self._tokens

    @property
    def projects_full(self):
        detailed_projects = {}
        for project_key,project in self.projects.items():
            detailed_projects[project_key] = {}
            detailed_projects[project_key]['project_key'] = project['project_key']
            detailed_projects[project_key]['display_name'] = project['display_name']
            detailed_projects[project_key]['roles'] = self.project_roles(project_key)
            detailed_projects[project_key]['groups'] = self.project_groups(project_key)
            detailed_projects[project_key]['users'] = self.project_users(project_key)
            detailed_projects[project_key]['repositories'] = self.project_repositories(project_key)
            detailed_projects[project_key]['watches'] = self.project_watches(project_key)
        return detailed_projects

    @property
    def service_accounts(self):
        if not self._service_accounts:
            self._service_accounts = self._get_all_service_accounts()
        return self._service_accounts

    def _requests_get(self, url):
        try:
            session = getattr(self.session_storage, 'session', None)
            if session is None:
                session = requests.Session()
                setattr(self.session_storage, 'session', session)
            response = session.get(
                url,
                headers={"Authorization": "Bearer " + self.token},
                verify=self.ssl_verify
            )
        except Exception as ex:
            error = {'errors': '{}'.format(ex)}
            raise ValueError(json.dumps(error, indent=2))

        if response.status_code != requests.codes.ok:
            raise ValueError(response.text)

        return json.loads(response.text)

    def _get_all_projects(self):
        url = self.url + '/access/api/v1/projects'
        projects = self._requests_get(url)
        projects_dict = {}
        for project in projects:
            projects_dict[project['project_key']] = project
        return projects_dict

    def _get_all_users(self):
        url = self.url + '/access/api/v2/users'
        all_users = self._requests_get(url)['users']
        usernames = [ user['username'] for user in all_users ]
        with ThreadPoolExecutor(max_workers=self.concurrent_workers) as executor:
            user_list = list(executor.map(self.user, usernames))

        users = {}
        for user in user_list:
            users[user['username']] = user
        return users

    def _get_all_groups(self):
        url = self.url + '/access/api/v2/groups'
        all_groups = self._requests_get(url)['groups']
        group_names = [ group['group_name'] for group in all_groups ]
        with ThreadPoolExecutor(max_workers=self.concurrent_workers) as executor:
            group_list = list(executor.map(self.group, group_names))

        groups = {}
        for group in group_list:
            groups[group['name']] = group
        return groups

    def _get_repository(self, repo_key):
        url = self.url + '/artifactory/api/repositories/' + repo_key
        return self._requests_get(url)

    def _get_all_repositories(self):
        all_repos = []
        url = self.url + '/artifactory/api/repositories'
        repositories = self._requests_get(url)
        repo_keys = [ repository['key'] for repository in repositories ]
        with ThreadPoolExecutor(max_workers=self.concurrent_workers) as executor:
            all_repos = list(executor.map(self._get_repository, repo_keys))

        return all_repos

    def _get_all_tokens(self):
        url = self.url + '/access/api/v1/tokens'
        tokens = self._requests_get(url)
        return tokens['tokens']

    def _get_all_service_accounts(self):
        groups = self.groups
        svc_accounts = [
            group for group_name,group in groups.items() 
            if group_name.startswith('svc-')
        ]
        return svc_accounts

    def user(self, username):
        url = self.url + '/access/api/v2/users/' + username
        user = self._requests_get(url)
        return user

    def group(self, group_name):
        url = self.url + '/access/api/v2/groups/' + group_name
        group = self._requests_get(url)
        return group
    
    def project_roles(self, project_key):
        url = self.url + '/access/api/v1/projects/' + project_key + '/roles'
        return self._requests_get(url)

    def project_groups(self, project_key):
        url = self.url + '/access/api/v1/projects/' + project_key + '/groups'
        groups = self._requests_get(url)['members']
        project_groups = []
        for group in groups:
            group_users = []
            for key,value in self.users.items():
                if group['name'] in value['groups']:
                    group_users.append(value)
            group['members'] = group_users
            project_groups.append(group)
        return project_groups

    def project_users(self, project_key):
        url = self.url + '/access/api/v1/projects/' + project_key + '/users'
        users = self._requests_get(url)['members']
        project_users = []
        for user in users:
            user_details = self.users[user['name']]
            user_details['roles'] = user['roles']
            project_users.append(user_details)
        return project_users

    def project_repositories(self, project_key):
        project_repositories = []
        repositories = self.repositories
        for repository in repositories:
            if repository['projectKey'] == project_key:
                project_repositories.append(repository)
        return project_repositories

    def project_watches(self, project_key):
        x = xray.Xray(
            url=self.url, 
            token=self.token, 
            ssl_verify=self.ssl_verify,
            concurrent_workers=self.concurrent_workers
        )
        watches = x.watches
        new_watches = []
        for _,watch in watches.items():
            if 'project_key' in watch['general_data'] and \
            watch['general_data']['project_key'] == project_key:
                new_watches.append(watch)
        return new_watches

    def repositories_by_package_type(self, package_type):
        package_types = [
            'alpine','bower','cargo','chef','cocoapods','composer','conan',
            'conda','cran','debian','docker','gems','generic',
            'gitlfs','go','gradle','helm','ivy','maven','npm','nuget','opkg',
            'pub','puppet','pypi','rpm','sbt','swift','terraformbackend',
            'terraform_module','terraform_provider','vagrant'
        ]

        if package_type not in package_types:
            raise ValueError('Invalid package type.')

        repositories = [
            repository for repository in self.repositories 
            if repository['packageType'] == package_type
        ]

        return repositories

    def project_info(self, project_key):
        projects = self.projects
        return projects[project_key]
    
    def project_info_full(self, project_key):
        projects = self.projects_full
        return projects[project_key]
