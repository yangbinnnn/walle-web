# -*- coding: utf-8 -*-
"""

    walle-web

    :copyright: © 2015-2017 walle-web.io
    :created time: 2017-03-25 11:15:01
    :author: wushuiyong@walle-web.io
"""

from flask import request, current_app, abort
from walle.api.api import SecurityResource
from walle.form.task import TaskForm
from walle.model.task import TaskModel
from walle.model.project import ProjectModel
from walle.model.space import SpaceModel
from walle.service.extensions import permission
from walle.service.rbac.role import *
from walle.service.notice import Notice


class TaskAPI(SecurityResource):
    actions = ['audit', 'reject', 'rollback']

    def get(self, task_id=None):
        """
        fetch project list or one item
        /project/<int:project_id>
        :return:
        """
        super(TaskAPI, self).get()

        return self.item(task_id) if task_id else self.list()

    def list(self):
        """
        fetch project list
        :return:
        """
        page = int(request.args.get('page', 0))
        page = page - 1 if page else 0
        size = int(request.args.get('size', 10))
        kw = request.values.get('kw', '')

        user_id = request.values.get('user_id', '')
        user_id = user_id.split(',') if user_id else []

        task_list, count = TaskModel().list(page=page, size=size, kw=kw, space_id=self.space_id, user_id=user_id)
        return self.list_json(list=task_list, count=count, enable_create=permission.role_upper_reporter() and current_user.role != SUPER)

    def item(self, task_id):
        """
        获取某个用户组
        :param id:
        :return:
        """

        task_model = TaskModel(id=task_id)
        task_info = task_model.item()
        if not task_info:
            return self.render_json(code=-1)
        return self.render_json(data=task_info)

    def post(self):
        """
        create a task
        /task/
        :return:
        """
        super(TaskAPI, self).post()

        form = TaskForm(request.form, csrf=False)
        if form.validate_on_submit():
            task_new = TaskModel()
            data = form.form2dict()
            task_new_info = task_new.add(data)
            if not task_new_info:
                return self.render_json(code=-1)

            # 待审核
            try:
                if task_new_info['status'] == TaskModel.status_new:
                    project_info = ProjectModel(id=task_new_info['project_id']).item()
                    space_id = project_info['space_id']
                    space_info = SpaceModel(id=space_id).item()
                    task_url =  Notice.task_url(project_space=space_info['name'], task_id=task_new_info['id'])
                    notice_info = {
                        'title': '新上线单需要审核',
                        'username': current_user.username,
                        'project_name': project_info['name'],
                        'task_id': task_new_info['id'],
                        'task_url': task_url,
                        'task_name': task_new_info['name'],
                        'branch': task_new_info['branch'],
                        'commit': task_new_info['commit_id'],
                        'tag': task_new_info['tag'],
                        'repo_mode': project_info['repo_mode'],
                    }
                    Notice.create(Notice.by_dingding).audit_task(project_info, notice_info)
            except:
                pass

            return self.render_json(data=task_new_info)
        else:
            return self.render_error(code=Code.form_error, message=form.errors)

    def put(self, task_id, action=None):
        """
        update task
        /task/<int:id>
        :return:
        """
        super(TaskAPI, self).put()

        if action:
            if action in self.actions:
                self_action = getattr(self, action.lower(), None)
                return self_action(task_id=task_id)
            else:
                abort(404)
        else:
            return self.update(task_id=task_id)

    def update(self, task_id):
        form = TaskForm(request.form, csrf=False)
        form.set_id(task_id)
        if form.validate_on_submit():
            task = TaskModel().get_by_id(task_id)
            data = form.form2dict()
            # a new type to update a model
            ret = task.update(data)
            return self.render_json(data=task.item())
        else:
            return self.render_error(code=Code.form_error, message=form.errors)

    def delete(self, task_id):
        """
        remove an task
        /task/<int:id>
        :return:
        """
        super(TaskAPI, self).delete()

        task_model = TaskModel(id=task_id)
        task_model.remove(task_id)

        return self.render_json(message='')

    def audit(self, task_id):
        """
        审核任务
        :param task_id:
        :return:
        """
        task = TaskModel().get_by_id(task_id)
        ret = task.update({'status': TaskModel.status_pass})
        return self.render_json(data=task.item(task_id))

    def reject(self, task_id):
        """
        审核任务
        :param task_id:
        :return:
        """
        task = TaskModel().get_by_id(task_id)
        ret = task.update({'status': TaskModel.status_reject})
        return self.render_json(data=task.item(task_id))

    def rollback(self, task_id):
        """
        回滚任务
        :param task_id:
        :return:
        """

        task = TaskModel.get_by_id(task_id).to_dict()
        filters = {
            TaskModel.link_id == task['ex_link_id'],
            TaskModel.id < task_id,
        }
        ex_task = TaskModel().query.filter(*filters).first()

        if not ex_task:
            raise WalleError(code=Code.rollback_error)

        task['id'] = None
        task['name'] = task['name'] + '-回滚此次上线'
        task['link_id'] = task['ex_link_id']
        task['ex_link_id'] = ''
        task['is_rollback'] = 1
        task['status'] = TaskModel.task_default_status(task['project_id'])

        # rewrite commit/tag/branch
        ex_task = ex_task.to_dict()
        task['commit_id'] = ex_task['commit_id']
        task['branch'] = ex_task['branch']
        task['tag'] = ex_task['tag']

        task_new = TaskModel()
        task_new_info = task_new.add(dict(task))

        return self.render_json(data=task_new_info)
