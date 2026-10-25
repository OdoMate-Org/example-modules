/** @odoo-module **/

import { Component, onWillStart, proxy } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

function iconInfo(menu) {
    const webIcon = menu.webIcon;
    if (webIcon && typeof webIcon === "object") {
        return { type: "font", ...webIcon, iconClass: webIcon.iconClass || webIcon.icon };
    }
    let data = menu.webIconData;
    if (data) {
        if (!data.startsWith("data:") && !data.startsWith("/")) {
            const mimetype = menu.webIconDataMimetype || "image/png";
            data = `data:${mimetype};base64,${data}`;
        }
        return { type: "image", src: data };
    }
    if (typeof webIcon === "string") {
        const parts = webIcon.split(",");
        if (parts.length === 3) {
            const [iconClass, color, backgroundColor] = parts;
            return { type: "font", iconClass, color, backgroundColor };
        }
        if (parts.length === 2) {
            return { type: "image", src: `/${parts[0]}/${parts[1]}` };
        }
    }
    return { type: "font", iconClass: "fa fa-cube", color: "#FFFFFF", backgroundColor: "#71639E" };
}

export class AppsDashboard extends Component {
    static template = "app_dashboard.AppsDashboard";

    setup() {
        this.orm = useService("orm");
        this.menu = useService("menu");
        this.notification = useService("notification");
        this.state = proxy({ apps: [], search: "" });
        this.draggedAppId = null;
        onWillStart(() => this.loadApps());
    }

    async loadApps() {
        const data = await this.orm.call("res.users", "get_app_dashboard_data", []);
        const apps = [];
        for (const app of data.apps) {
            const menu = this.menu.getMenu(app.id);
            if (!menu) {
                continue;
            }
            apps.push({
                id: app.id,
                name: menu.name || app.name,
                isFavorite: app.is_favorite,
                isPriority: app.is_priority,
                icon: iconInfo(menu),
                menu,
            });
        }
        this.state.apps = apps;
    }

    get filteredApps() {
        const term = this.state.search.trim().toLowerCase();
        if (!term) {
            return this.state.apps;
        }
        return this.state.apps.filter((app) => app.name.toLowerCase().includes(term));
    }

    get favoriteApps() {
        return this.filteredApps.filter((app) => app.isFavorite);
    }

    get otherApps() {
        return this.filteredApps.filter((app) => !app.isFavorite);
    }

    iconStyle(app) {
        if (app.icon.type !== "font") {
            return "";
        }
        return `background-color: ${app.icon.backgroundColor}; color: ${app.icon.color};`;
    }

    starTitle(app) {
        return app.isFavorite ? _t("Remove from favorites") : _t("Add to favorites");
    }

    onSearchInput(ev) {
        this.state.search = ev.target.value;
    }

    async onOpenApp(app) {
        this.orm.call("res.users", "register_app_open", [app.id]).catch(() => {});
        await this.menu.selectMenu(app.menu);
    }

    async onToggleFavorite(app) {
        const isFavorite = await this.orm.call("res.users", "toggle_app_favorite", [app.id]);
        const wanted = !app.isFavorite;
        app.isFavorite = isFavorite;
        if (isFavorite !== wanted) {
            this.notification.add(_t("This app is no longer available to you."), { type: "warning" });
            await this.loadApps();
        }
    }

    get canReorder() {
        return !this.state.search.trim();
    }

    onTileDragStart(ev, app) {
        if (!this.canReorder) {
            return;
        }
        this.draggedAppId = app.id;
        ev.dataTransfer.effectAllowed = "move";
    }

    onTileDragOver(ev) {
        if (this.canReorder && this.draggedAppId !== null) {
            ev.preventDefault();
        }
    }

    async onTileDrop(ev, targetApp) {
        ev.preventDefault();
        const draggedAppId = this.draggedAppId;
        this.draggedAppId = null;
        if (!this.canReorder || draggedAppId === null || draggedAppId === targetApp.id) {
            return;
        }
        const others = this.otherApps;
        const ids = others.map((app) => app.id);
        const fromIndex = ids.indexOf(draggedAppId);
        const toIndex = ids.indexOf(targetApp.id);
        if (fromIndex === -1 || toIndex === -1) {
            return;
        }
        ids.splice(toIndex, 0, ids.splice(fromIndex, 1)[0]);
        const appById = new Map(this.state.apps.map((app) => [app.id, app]));
        const reordered = ids.map((id) => appById.get(id));
        this.state.apps = [...this.favoriteApps, ...reordered];
        await this.orm.call("res.users", "reorder_apps", [ids]);
    }
}

registry.category("actions").add("app_dashboard.AppsDashboard", AppsDashboard);
