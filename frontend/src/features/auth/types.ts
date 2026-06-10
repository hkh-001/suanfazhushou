export type AuthUser = {
  id: string;
  email: string;
  username: string;
  learning_stage: string;
  target_track: string;
  is_dev_user: boolean;
};

export type AuthUserResponse = {
  data: AuthUser;
};

export type AuthRegisterPayload = {
  email: string;
  username: string;
  password: string;
};

export type AuthLoginPayload = {
  email: string;
  password: string;
};

export type LogoutResponse = {
  data: {
    success: boolean;
  };
};
