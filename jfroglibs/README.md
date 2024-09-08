# pwcjfrog
Library providing methods for acquiring Artifactory and Xray information.

## Usage
The are several ways to use this library. One way is to copy and include this pwcjfrog directory into the main code and import pwcjfrog.

Another way is to install the library using pip. For example, to install directly from Github, run: `pip install git+https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/pwc-gx-ngioa-sds/artefact-mgmt-reporting.git#subdirectory=libs`. Or add `pwcjfrog @ git+https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/pwc-gx-ngioa-sds/artefact-mgmt-reporting.git#subdirectory=libs` to requirements.txt file and then run `pip install -r ./requirements.txt`.

It can also be uploaded to a private python repository such as Artifactory. To upload to Artifactory, first need to create a package. To create a package, run `cd .. && python setup.py sdist`. Then, upload the tar file in dist directory to Artifactory.

Example code:
```
import pwcjfrog

art = pwcjfrog.Artifactory(url='ARTIFACTORY_URL', token='ARTIFACTORY_TOKEN', ssl_verify=True)

projects = art.projects
print(projects)

project_users = art.project_users('g00003')
print(project_users)

x = pwcjfrog.Xray(url='ARTIFACTORY_URL', token='ARTIFACTORY_TOKEN', ssl_verify=True)

watches = x.watches
print(watches)
```

## Classes
* Artifactory
* Xray

## Artifactory Attributes and Methods
### Attributes:
`projects` - contains all the projects in the cluster.  
`users` - contains all the users in the cluster.  
`groups` - contains all the groups in the cluster.  
`repositories` - contains all the repositories in the cluster.  
`tokens` - contains all the tokens in the cluster.  
`projects_full` - contains all the projects in the cluster along with users, groups, repositories, and watches that belong to individual projects.  
`service_accounts` - contains all the service accounts in the cluster.  

### Methods:
`project_roles(project_key)` - returns the roles belonging to specific project.  
`project_groups(project_key)` - returns the groups belonging to specific project.  
`project_users(project_key)` - returns the users belonging to specific project.  
`project_repositories(project_key)` - returns the repositories belonging to specific project.  
`project_watches(project_key)` - returns the Xray watches belonging to specific project.  
`repositories_by_package_type(package_type)` - returns all repositories with types specified by package_type. 
`project_info(project_key)` - returns info about a project specified by project key.  
`project_info_full(project_key)` - returns detailed info about a project specified by project key.  

## Xray Attributes and Methods
### Attributes:
`watches` - contains all the watches in the Xray cluster.  