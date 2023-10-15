import { Interface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/LoadingOverlay";
import Guacamole from "guacamole-common-js";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, state } from "lit/decorators.js";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

enum GuacClientState {
    IDLE = 0,
    CONNECTING = 1,
    WAITING = 2,
    CONNECTED = 3,
    DISCONNECTING = 4,
    DISCONNECTED = 5,
}

@customElement("ak-rac")
export class RacInterface extends Interface {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFPage,
            PFContent,
            AKGlobal,
            css`
                :host {
                    height: 100vh;
                    width: 100vw;
                    overflow: hidden;
                }
                canvas {
                    z-index: 1 !important;
                }
                .container {
                    height: 100vh;
                }
                ak-loading-overlay {
                    z-index: 5;
                }
            `,
        ];
    }

    client?: Guacamole.Client;
    tunnel?: Guacamole.Tunnel;

    @state()
    container?: HTMLElement;

    @state()
    clientState?: GuacClientState;

    firstUpdated(): void {
        // TODO: Remove
        const app = "test";
        const wsUrl = `${window.location.protocol.replace("http", "ws")}//${
            window.location.host
        }/ws/rac/${app}/`;
        this.tunnel = new Guacamole.WebSocketTunnel(wsUrl);
        this.client = new Guacamole.Client(this.tunnel);
        this.client.onerror = (err) => {
            console.debug("authentik/rac: error: ", err);
        };
        this.client.onstatechange = (state) => {
            this.clientState = state;
            if (state === GuacClientState.CONNECTED) {
                this.onConnected();
            }
        };
        this.container = this.client.getDisplay().getElement();
        this.initMouse(this.container);
        this.initKeyboard();
        const params = new URLSearchParams();
        params.set(
            "screen_width",
            (this.getBoundingClientRect().width * window.devicePixelRatio).toString(),
        );
        params.set(
            "screen_height",
            (this.getBoundingClientRect().height * window.devicePixelRatio).toString(),
        );
        params.set("screen_dpi", (window.devicePixelRatio * 96).toString());
        this.client.connect(params.toString());
    }

    onConnected(): void {
        console.debug("authentik/rac: connected");
        this.client?.sendSize(
            this.getBoundingClientRect().width * window.devicePixelRatio,
            this.getBoundingClientRect().height * window.devicePixelRatio,
        );
    }

    initMouse(container: HTMLElement): void {
        const mouse = new Guacamole.Mouse(container);
        const handler = (mouseState: Guacamole.Mouse.State, scaleMouse = false) => {
            if (!this.client) return;

            if (scaleMouse) {
                mouseState.y = mouseState.y / this.client.getDisplay().getScale();
                mouseState.x = mouseState.x / this.client.getDisplay().getScale();
            }

            this.client.sendMouseState(mouseState);
        };
        mouse.onmouseup = mouse.onmousedown = (mouseState) => {
            this.container?.focus();
            handler(mouseState);
        };
        mouse.onmousemove = (mouseState) => {
            handler(mouseState, true);
        };
    }

    initKeyboard(): void {
        const keyboard = new Guacamole.Keyboard(document);
        keyboard.onkeydown = (keysym) => {
            this.client?.sendKeyEvent(1, keysym);
        };
        keyboard.onkeyup = (keysym) => {
            this.client?.sendKeyEvent(0, keysym);
        };
    }

    render(): TemplateResult {
        return html`
            ${this.clientState !== GuacClientState.CONNECTED
                ? html` <ak-loading-overlay></ak-loading-overlay> `
                : html``}
            <div class="container">${this.container}</div>
        `;
    }
}
