# -*- coding: utf-8 -*-


from openerp.osv import fields, osv
from openerp import tools
from openerp.tools.safe_eval import safe_eval as eval
import json
import base64



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
        """
            Query fetching grouped by task owner
            :returns query structure as required for View.
        """

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


    def prepare_json_export(self, cr, uid):
        """
            Prepares JSON file for exporting
            :returns downloadable report link
        """

        rptLine = self.pool.get('report.project.task.status.lines')

        cr.execute(rptLine._select(forJSON=True))
        res = cr.dictfetchall()
        data = {'result': res}
        file_name = 'report_task_status.json'

        datastr = json.dumps(data)
        out = base64.b64encode(datastr.encode('utf-8'))

        attachment_id = self.pool.get('ir.attachment').create(cr, uid,
            {
                'name': file_name,
                'datas': out,
                'datas_fname': file_name,
                'res_model': self._name,
                'res_id': 1,
                'type': 'binary'
            })

        return {
                   'type': 'ir.actions.report.xml',
                   'report_type': 'controller',
                   'report_file': '/web/binary/saveas?model=ir.attachment&field=datas&filename_field=datas_fname&id=%s'%(attachment_id)
        }


class report_project_task_status_lines(osv.osv):
    _name = "report.project.task.status.lines"
    _description = "Tasks Status by user and project - lines"
    _auto = False
    _rec_name = 'project_id'

    _columns = {
        'user_id': fields.many2one('res.users', 'Task Owner', readonly=True),
        'project_id': fields.many2one('project.project', 'Project', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'nbr_open'  : fields.integer('Open', help='Count of Open Tasks', readonly=True),
        'nbr_open_delay'  : fields.integer('Delay', help='Count of Delayed (Open)', readonly=True),
        'nbr_done_month'  : fields.integer('Finish-Month', help='Count of Done (This Month)', readonly=True),
        'nbr_done_lastwk' : fields.integer('Finish-Week', help='Count of Done (Last Week)', readonly=True),
    }


    def _select(self, forJSON=False):
        """
            Query for fetching detailed info about Task status
            :returns query structure as required either for View or JSON file.
        """

        if forJSON:
            col_str = """             
 
            SELECT row_number() OVER () as id
                 , p.name as "User"
                 , aa.name as "Project"
                 , sum(coalesce(nbr_open,0)) as "Open"
                 , sum(coalesce(nbr_open_delay,0)) as "Delay"
                 , sum(coalesce(nbr_done_month,0)) as "Finish-Month"
                 , sum(coalesce(nbr_done_lastwk,0)) as "Finish-Week"
            """

            frm_str = """ JOIN res_users u on u.id = user_id
                          JOIN res_partner p on p.id = u.partner_id  
                          JOIN project_project pp on pp.id = project_id  
                          JOIN account_analytic_account aa on aa.id = pp.analytic_account_id
                          GROUP BY p.id, aa.id, y.company_id
                     """

        else:
            col_str = """
     
                SELECT row_number() OVER () as id
                     , user_id
                     , project_id
                     , sum(coalesce(nbr_open,0)) as nbr_open
                     , sum(coalesce(nbr_open_delay,0)) as nbr_open_delay
                     , sum(coalesce(nbr_done_month,0)) as nbr_done_month
                     , sum(coalesce(nbr_done_lastwk,0)) as nbr_done_lastwk
                     , company_id
                """
            frm_str = """ GROUP BY y.user_id, y.project_id, y.company_id"""


        select_str = col_str + """ 
            FROM (
                
               -- OPEN TASKS ---
                SELECT t.user_id
                      , t.project_id
                      , count(t.id) as nbr_open
                      , 0 as nbr_open_delay
                      , 0 as nbr_done_month
                      , 0 as nbr_done_lastwk
                      , t.company_id
                FROM project_task t
                JOIN project_task_type s on s.id = t.stage_id
                WHERE t.active = 'true' 
                AND t.stage_id not in ( select distinct x.type_id
                                    from (	  
                                    select sp.project_id
                                           , s.sequence
                                           , sp.type_id
                                           , row_number() over (partition by project_id order by s.sequence desc, s.id) rn
                                    from project_task_type s
                                    join project_task_type_rel sp on sp.type_id = s.id
                                    join project_project p on p.id = sp.project_id
                                )x
                                where x.type_id in (7,8) or x.sequence >= 100)
                GROUP BY t.user_id, t.project_id, t.company_id	
                UNION ALL
            
                -- OPEN DELAYED TASKS --
                SELECT t.user_id
                      , t.project_id
                      , 0 as nbr_open
                      , count(t.id) as nbr_open_delay
                      , 0 as nbr_done_month
                      , 0 as nbr_done_lastwk
                      , t.company_id
                FROM project_task t
                JOIN project_task_type s on s.id = t.stage_id
                WHERE t.active = 'true' 
                AND t.stage_id not in ( select distinct x.type_id
                                    from (	  
                                    select sp.project_id
                                           , s.sequence
                                           , sp.type_id
                                           , row_number() over (partition by project_id order by s.sequence desc, s.id) rn
                                    from project_task_type s
                                    join project_task_type_rel sp on sp.type_id = s.id
                                    join project_project p on p.id = sp.project_id
                                )x
                                where x.type_id in (7,8) or x.sequence >= 100)
                AND coalesce(t.date_deadline, now()::date) < now()::date
                GROUP BY t.user_id, t.project_id, t.company_id		 
                UNION ALL
            
                -- FINISHED CURRENT MONTH --
                SELECT t.user_id
                      , t.project_id
                      , 0 as nbr_open
                      , 0 as nbr_open_delay
                      , count(t.id) as nbr_done_month
                      , 0 as nbr_done_lastwk
                      , t.company_id
                FROM project_task t
                JOIN project_task_type s on s.id = t.stage_id
                WHERE t.active = 'true' 
                AND t.stage_id in ( select distinct x.type_id
                                    from (	  
                                    select sp.project_id
                                           , s.sequence
                                           , sp.type_id
                                           , row_number() over (partition by project_id order by s.sequence desc, s.id) rn
                                    from project_task_type s
                                    join project_task_type_rel sp on sp.type_id = s.id
                                    join project_project p on p.id = sp.project_id
                                )x
                                where x.type_id in (7,8) or x.sequence >= 100)
                AND coalesce(t.date_last_stage_update, now()::date) between (date_trunc('month', now()::date)) 
                            and (date_trunc('month', now()::date) + interval '1 month - 1 day')
                GROUP BY t.user_id, t.project_id, t.company_id		
                UNION ALL	
            
                -- FINISHED LAST WEEK --
                SELECT t.user_id
                      , t.project_id
                      , 0 as nbr_open
                      , 0 as nbr_open_delay
                      , 0 as nbr_done_month
                      , count(t.id) as nbr_done_lastwk
                      , t.company_id
                FROM project_task t
                JOIN project_task_type s on s.id = t.stage_id
                WHERE t.active = 'true' 
                AND t.stage_id in ( select distinct x.type_id
                                    from (	  
                                    select sp.project_id
                                           , s.sequence
                                           , sp.type_id
                                           , row_number() over (partition by project_id order by s.sequence desc, s.id) rn
                                    from project_task_type s
                                    join project_task_type_rel sp on sp.type_id = s.id
                                    join project_project p on p.id = sp.project_id
                                )x
                                where x.type_id in (7,8) or x.sequence >= 100)
                AND coalesce(t.date_last_stage_update, now()::date) between (date_trunc('week', now()::date) + interval '- 7 day') 
                             and (date_trunc('week', now()::date) + interval '- 1 day')
                GROUP BY t.user_id, t.project_id, t.company_id
            )y
            """ + frm_str
        return select_str

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, self._table)
        sql = """CREATE or REPLACE VIEW %s as ( %s)""" % (self._table, self._select())
        cr.execute(sql)