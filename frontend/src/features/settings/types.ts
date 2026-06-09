export type AISettingsSource = "runtime" | "env" | "none";

export type AISettingsStatus = {
  configured: boolean;
  source: AISettingsSource;
  provider: string;
  base_url: string | null;
  model: string | null;
  api_key_set: boolean;
  runtime_settings_enabled: boolean;
};

export type AISettingsResponse = {
  data: AISettingsStatus;
};

export type AISettingsPayload = {
  base_url: string;
  api_key: string;
  model: string;
};

export type AISettingsTestResponse = {
  data: {
    ok: boolean;
  };
};
