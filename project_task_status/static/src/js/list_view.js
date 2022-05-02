
openerp.project_task_status = function (instance){

    var QWeb = openerp.web.qweb;
    _t = instance.web._t;
    var self = this;
    var RptTaskStatus = new openerp.Model('report.project.task.status');

    openerp.web.ListView.include({
        load_list: function(data) {
            this._super(data);
            if (this.$buttons) {
                this.$buttons.find('.btn_export_json').off().click(this.proxy('do_action_export_json')) ;
                console.log('Button found !!...');
                }
            },

            do_action_export_json: function () {
                RptTaskStatus.call('prepare_json_export').then(function (result) {
                    console.log("Called Method !!")
                });

//                this.do_action({
//                    type: "ir.actions.act_window",
//                    name: 'Export in JSON',
//                    res_model: 'report.project.task.status',
//                    view_type: 'form',
//                    view_mode: 'form',
//                    target: 'new',
//                    views: [[false, 'form']],
//                    flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}});

                return { 'type': 'ir.actions.client',
                    'tag': 'reload', } }

        });
}

