/** @odoo-module **/

import { Component, onWillStart, proxy, signal } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useAutofocus, useService } from "@web/core/utils/hooks";

const LAUNCHPAD_MENU_XMLID = "odomate_launchpad.menu_odomate_launchpad_root";
const USAGE_MODEL = "odomate.launchpad.usage";
const PIN_MODEL = "odomate.launchpad.pin";

function iconImageSource(app) {
    const data = app.webIconData || app.web_icon_data;
    if (data) {
        if (data.startsWith("data:")) {
            return data;
        }
        const clean = data.replace(/\s/g, "");
        const mimetype =
            app.webIconDataMimetype ||
            app.web_icon_data_mimetype ||
            (clean.startsWith("PHN2") || clean.startsWith("PD94") ? "image/svg+xml" : "image/png");
        return `data:${mimetype};base64,${clean}`;
    }
    const webIcon = app.webIcon || app.web_icon;
    if (typeof webIcon === "string") {
        const [moduleName, path] = webIcon.split(",");
        if (path && path.includes("/")) {
            return `/${moduleName}/${path}`;
        }
    }
    return null;
}

function iconFont(app) {
    const webIcon = app.webIcon || app.web_icon;
    let iconClass, color, backgroundColor;
    if (webIcon && typeof webIcon === "object") {
        ({ iconClass, color, backgroundColor } = webIcon);
    } else if (typeof webIcon === "string") {
        [iconClass, color, backgroundColor] = webIcon.split(",");
    }
    // "module,path/to/icon.png" is an image reference, not a font icon.
    if (!iconClass || !color || color.includes("/")) {
        return null;
    }
    // Odoo 20 renders app font icons as <i class="oi" data-icon="name"/>.
    iconClass = iconClass.replace(/^(fa|oi)\s+(fa|oi)-/, "");
    return {
        iconClass,
        style: `color: ${color || "#ffffff"}; background-color: ${backgroundColor || "#714b67"};`,
    };
}

export class Launchpad extends Component {
    static template = "odomate_launchpad.Launchpad";
    searchInput = signal.ref();

    setup() {
        this.orm = useService("orm");
        this.menuService = useService("menu");
        this.notification = useService("notification");
        this.state = proxy({
            query: "",
            tiles: [],
            isHome: false,
            loading: true,
        });
        useAutofocus({ ref: this.searchInput });
        onWillStart(() => this.loadTiles());
    }

    get availableApps() {
        return this.menuService
            .getApps()
            .filter((app) => app.xmlid !== LAUNCHPAD_MENU_XMLID);
    }

    get visibleTiles() {
        const query = this.state.query.trim().toLocaleLowerCase();
        if (!query) {
            return this.state.tiles;
        }
        return this.state.tiles.filter((tile) =>
            tile.name.toLocaleLowerCase().includes(query)
        );
    }

    makeTile(app, pinned, count) {
        const fontIcon = iconFont(app);
        return {
            id: app.id,
            name: app.name,
            xmlid: app.xmlid || "",
            app,
            pinned,
            count,
            fontIcon,
            imageSrc: fontIcon ? null : iconImageSource(app),
            initial: (app.name || "?").trim().charAt(0).toLocaleUpperCase(),
        };
    }

    async loadTiles() {
        const apps = this.availableApps;
        const appsById = new Map(apps.map((app) => [app.id, app]));
        const result = await this.orm.call(USAGE_MODEL, "get_launchpad_state", [
            apps.map((app) => app.id),
        ]);
        const pinnedIds = new Set(result.pinned_ids);
        const orderedIds = result.ordered_ids.filter((id) => appsById.has(id));
        const seen = new Set(orderedIds);
        const leftovers = apps
            .filter((app) => !seen.has(app.id))
            .sort((a, b) => a.name.localeCompare(b.name))
            .map((app) => app.id);
        this.state.tiles = [...orderedIds, ...leftovers].map((id) =>
            this.makeTile(appsById.get(id), pinnedIds.has(id), result.counts[id] || 0)
        );
        this.state.isHome = result.is_home;
        this.state.loading = false;
    }

    async openApp(tile) {
        try {
            await this.orm.silent.call(USAGE_MODEL, "log_open", [tile.id]);
        } catch {
            // Usage logging is best-effort: it must never block opening the app.
        }
        await this.menuService.selectMenu(tile.app);
    }

    async togglePin(tile) {
        const pinned = await this.orm.call(PIN_MODEL, "toggle_pin", [tile.id]);
        this.notification.add(
            pinned ? _t("%s pinned to the top", tile.name) : _t("%s unpinned", tile.name),
            { type: "info" }
        );
        await this.loadTiles();
    }

    async setAsHome() {
        await this.orm.call(USAGE_MODEL, "set_launchpad_as_home", []);
        this.state.isHome = true;
        this.notification.add(
            _t("Launchpad will open after your next login."),
            { type: "success" }
        );
    }

    async resetHome() {
        await this.orm.call(USAGE_MODEL, "reset_launchpad_home", []);
        this.state.isHome = false;
        this.notification.add(
            _t("Launchpad is no longer your startup screen."),
            { type: "info" }
        );
    }

    onSearchInput(ev) {
        this.state.query = ev.target.value;
    }

    onSearchKeydown(ev) {
        if (ev.key === "Enter") {
            const [first] = this.visibleTiles;
            if (first) {
                this.openApp(first);
            }
        } else if (ev.key === "Escape") {
            this.state.query = "";
        }
    }

    pinTitle(tile) {
        return tile.pinned ? _t("Unpin %s", tile.name) : _t("Pin %s to the top", tile.name);
    }

    usageTitle(tile) {
        return _t("Opens in the last 30 days: %s", tile.count);
    }
}

registry.category("actions").add("odomate_launchpad.Launchpad", Launchpad);
