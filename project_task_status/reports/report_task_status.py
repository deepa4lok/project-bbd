# -*- coding: utf-8 -*-


from openerp.osv import fields, osv
from openerp import tools
from openerp.tools.safe_eval import safe_eval as eval



class report_project_task_status(osv.osv):
    _name = "report.project.task.status"
    _description = "Tasks Status by user and project"
    _auto = False

    _columns = {
        'name': fields.char('Status', readonly=True),
        'stage_id': fields.many2one('project.task.type', 'Stage'),
        'user_id': fields.many2one('res.users', 'Task Owner', readonly=True),
        'login': fields.char('Login', readonly=True),
    }

    def open_task_details(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'project_task_status', 'action_project_task_status_lines')
        id = result and result[1] or False

        result = act_obj.read(cr, uid, [id], context=context)[0]
        domain = eval(result['domain'])
        for case in self.browse(cr, uid, ids):
            domain.append(('user_id', '=', case.user_id.id))
            result['domain'] = domain
        return result


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
                , u.login
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


class report_project_task_status_lines(osv.osv):
    _name = "report.project.task.status.lines"
    _description = "Tasks Status by user and project - lines"
    _auto = False

    _columns = {
        'name': fields.char('Task Summary', readonly=True),
        'user_id': fields.many2one('res.users', 'Task Owner', readonly=True),
        'project_id': fields.many2one('project.project', 'Project', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'stage_id': fields.many2one('project.task.type', 'Stage'),
    }


    def _select(self):
        select_str = """

        select row_number() OVER () as id
                , t.user_id
                , t.project_id
                , t.name as name
                , t.company_id
                , t.stage_id as stage_id
        FROM project_task t
        WHERE t.active = 'true'

        """
        return select_str

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, self._table)
        sql = """CREATE or REPLACE VIEW %s as ( %s)""" % (self._table, self._select())
        cr.execute(sql)