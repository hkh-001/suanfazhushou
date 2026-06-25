export type AuthUser = {
  id: string;
  email: string | null;
  username: string | null;
  student_id: string;
  name: string;
  current_level: "beginner" | "elementary" | "popularization" | "improvement";
  goal_track: "course" | "lanqiao" | "icpc" | "self_study";
  goal_description: string | null;
  role: "user" | "admin";
  learning_stage: string;
  target_track: string;
  is_dev_user: boolean;
};

export type AuthUserResponse = {
  data: AuthUser;
};

export type AuthRegisterPayload = {
  student_id: string;
  password: string;
  name: string;
  current_level: AuthUser["current_level"];
  goal_track: AuthUser["goal_track"];
  goal_description?: string | null;
};

export type AuthLoginPayload = {
  student_id: string;
  password: string;
};

export type LogoutResponse = {
  data: {
    success: boolean;
  };
};
