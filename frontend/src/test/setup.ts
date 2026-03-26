import { config } from "@vue/test-utils";
import { createI18n } from "vue-i18n";

import { createI18nOptions } from "@/lib/i18n";

config.global.plugins = [createI18n(createI18nOptions("en", "en"))];
