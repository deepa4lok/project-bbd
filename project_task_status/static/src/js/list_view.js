
openerp.project_task_status = function (instance){

    var QWeb = openerp.web.qweb;
    _t = instance.web._t;
    var self = this;
    var RptTaskStatus = new openerp.Model('report.project.task.status');

    instance.web.ListView.include({
        load_list: function () {
            var self = this;
            var add_button = false;
            if (!this.$buttons) {
                add_button = true;
            }
            this._super.apply(this, arguments);
            if(add_button) {
                this.$buttons.on('click', '.btn_export_json', function() {
                    new instance.web.Model("report.project.task.status")
                        .call("prepare_json_export", [])
                        .then(function (result) {
                            self.do_action(result);
                        });

                    return false;
                });
            }
        }
    });

}

