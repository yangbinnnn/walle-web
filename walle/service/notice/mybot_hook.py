# -*- coding: utf-8 -*-
import json

import requests
from walle.model.project import ProjectModel
from urlparse import urlparse, parse_qs

# mybot://123.0.0.1/walle?auditor=123,456&groupid=123
def is_mybot_hook(notice_hook):
    return notice_hook.startswith('mybot://')

def _parser_hook_url(url):
    u = urlparse(url.replace('mybot://', 'http://'))
    query = u.query
    url = u.geturl().split('?')[0]
    qs = parse_qs(query)
    auditor = qs.get('auditor')[0].split(',')
    groupid = qs.get('groupid')[0]
    data = {
        'url': url,
        'auditor': auditor,
        'groupid': groupid,
    }
    return data


def mybot_deploy_task(project_info, notice_info):
    if notice_info['repo_mode'] == ProjectModel.repo_mode_tag:
        version = notice_info['tag']
    else:
        version = '%s/%s' % (notice_info['branch'], notice_info['commit'])
    
    data = {
        "msgtype": "deploy",
        "version": version,
        "project_info": project_info,
        "notice_info": notice_info,
    }
    '''
    上线单新建, 上线完成, 上线失败

    @param hook:
    @param notice_info:
        'title',
        'username',
        'project_name',
        'task_name',
        'branch',
        'commit',
        'is_branch',
    @return:
    '''
    headers = {'Content-Type': 'application/json;charset=UTF-8'}
    for hook in project_info['notice_hook'].split(';'):
        hook_conf = _parser_hook_url(hook)
        url = hook_conf.pop('url')
        data['mybot'] = hook_conf
        response = requests.post(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        # @todo增加可能错误到console中显示

    return True


def mybot_audit_task(project_info, notice_info):
    if notice_info['repo_mode'] == ProjectModel.repo_mode_tag:
        version = notice_info['tag']
    else:
        version = '%s/%s' % (notice_info['branch'], notice_info['commit'])
    
    data = {
        "msgtype": "audit",
        "version": version,
        "project_info": project_info,
        "notice_info": notice_info,
    }
    '''
    上线单新建, 上线完成, 上线失败

    @param hook:
    @param notice_info:
        'title',
        'username',
        'project_name',
        'task_name',
        'branch',
        'commit',
        'is_branch',
    @return:
    '''
    headers = {'Content-Type': 'application/json;charset=UTF-8'}
    for hook in project_info['notice_hook'].split(';'):
        hook_conf = _parser_hook_url(hook)
        url = hook_conf.pop('url')
        data['mybot'] = hook_conf
        response = requests.post(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        # @todo增加可能错误到console中显示

    return True
