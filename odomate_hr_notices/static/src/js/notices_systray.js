/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Dropdown } from "@web/core/dropdown/dropdown";

export class NoticesSystray extends Component {
    static template = "odomate_hr_notices.NoticesSystray";
    static components = { Dropdown };
    static props = [];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            announcements: [],
            reminders: [],
            announcementCount: 0,
            loading: false,
        });
        onWillStart(() => this.loadNotices());
    }

    async loadNotices() {
        this.state.loading = true;
        try {
            const result = await this.orm.call(
                "odomate.hr.announcement",
                "get_systray_notices",
                []
            );
            this.state.announcements = result.announcements || [];
            this.state.reminders = result.reminders || [];
            this.state.announcementCount = result.announcement_count || 0;
        } finally {
            this.state.loading = false;
        }
    }

    openRecord(resModel, resId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: resModel,
            res_id: resId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openAnnouncement(announcementId) {
        this.openRecord("odomate.hr.announcement", announcementId);
    }

    openReminder(reminderId) {
        this.openRecord("odomate.hr.reminder", reminderId);
    }
}

registry.category("systray").add(
    "odomate_hr_notices.NoticesSystray",
    { Component: NoticesSystray },
    { sequence: 50 }
);
