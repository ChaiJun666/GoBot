import { createApp } from "vue";

import App from "./App.vue";
import { createAppI18n } from "./lib/i18n";
import "./style.css";

createApp(App).use(createAppI18n()).mount("#app");
