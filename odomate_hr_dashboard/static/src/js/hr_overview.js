/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { _t } from "@web/core/l10n/translation";

export class HrOverview extends Component {
    static template = "odomate_hr_dashboard.HrOverview";
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        const year = new Date().getFullYear();
        this.state = useState({
            dateFrom: `${year}-01-01`,
            dateTo: `${year}-12-31`,
            loading: true,
            showPending: true,
            data: null,
        });
        onWillStart(() => this.loadOverview());
    }

    async loadOverview() {
        this.state.loading = true;
        this.state.data = await this.orm.call("odomate.hr.dashboard", "get_overview", [
            this.state.dateFrom,
            this.state.dateTo,
        ]);
        this.state.loading = false;
    }

    get tiles() {
        const data = this.state.data;
        if (!data) {
            return [];
        }
        return [
            {
                key: "headcount",
                label: _t("Headcount"),
                value: data.headcount,
                suffix: "",
                periodBound: false,
                action: data.actions.headcount,
            },
            {
                key: "joined",
                label: _t("Joined"),
                value: data.joined,
                suffix: "",
                periodBound: true,
                action: data.actions.joined,
            },
            {
                key: "left",
                label: _t("Left"),
                value: data.left,
                suffix: "",
                periodBound: true,
                action: data.actions.left,
            },
            {
                key: "off_today",
                label: _t("Off today"),
                value: data.off_today,
                suffix: "",
                periodBound: false,
                action: data.actions.off_today,
            },
            {
                key: "turnover",
                label: _t("Turnover"),
                value: data.turnover_rate,
                suffix: "%",
                periodBound: true,
                action: data.actions.turnover,
            },
        ];
    }

    get entries() {
        return [
            {
                key: "movements",
                label: _t("Joiners and leavers"),
                icon: "fa-exchange",
                action: "odomate_hr_dashboard.action_hr_movement",
            },
            {
                key: "absence",
                label: _t("Absence by employee"),
                icon: "fa-user-times",
                action: "odomate_hr_dashboard.action_hr_absence_factor",
            },
            {
                key: "departments",
                label: _t("Headcount by department"),
                icon: "fa-sitemap",
                action: "odomate_hr_dashboard.action_hr_department_headcount",
            },
            {
                key: "pending",
                label: _t("Waiting for approval"),
                icon: "fa-clock-o",
                action: false,
            },
        ];
    }

    onDateFromChange(ev) {
        this.state.dateFrom = ev.target.value;
        this.loadOverview();
    }

    onDateToChange(ev) {
        this.state.dateTo = ev.target.value;
        this.loadOverview();
    }

    openAction(actionId) {
        if (actionId) {
            this.action.doAction(actionId);
        }
    }

    onEntryClick(entry) {
        if (entry.action) {
            this.action.doAction(entry.action);
        } else {
            this.state.showPending = !this.state.showPending;
        }
    }
}

registry.category("actions").add("odomate_hr_dashboard.hr_overview", HrOverview);
