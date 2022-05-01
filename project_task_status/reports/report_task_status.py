# -*- coding: utf-8 -*-


from openerp.osv import fields, osv
from openerp import tools


class report_project_task_status(osv.osv):
    _name = "report.project.task.status"
    _description = "Tasks Status by user and project"
    _auto = False
    # _order = 'state, user_id, project_id'

    _columns = {
        'name': fields.char('Status', readonly=True),
        'stage_id': fields.many2one('project.task.type', 'Stage'),
        'user_id': fields.many2one('res.users', 'Task Owner', readonly=True),
        'login': fields.char('Login', readonly=True),
        # 'project_id': fields.many2one('project.project', 'Project', readonly=True),
        # 'company_id': fields.many2one('res.company', 'Company', readonly=True),
        # 'state': fields.selection([('normal', 'In Progress'),('blocked', 'Blocked'),('done', 'Ready for next stage')],'Status', readonly=True),
    }


    def _select(self):
        select_str = """ 

        SELECT row_number() OVER () as id
            , s.id as stage_id
            , s.name
            , usr.user_id
            , usr.login
        FROM project_task_type s
        INNER JOIN 
        (
            select distinct t.user_id
                , t.stage_id
              task  , u.login
            from project_task t
            left outer join res_users u on u.id = t.user_id
            where t.active is true
        )usr on usr.stage_id = s.id
        ORDER BY s.sequence

        """
        return select_str




    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, self._table)
        sql = """CREATE or REPLACE VIEW %s as ( %s)""" % (self._table, self._select())
        cr.execute(sql)




