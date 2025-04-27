import React, { useEffect } from "react";
import App from "../../app";
import { useDispatch } from "react-redux";
import { ActionType } from "../../utils/helpers/types";
import { useI18n } from "../../utils/i18n";

const AuthWithNothing: React.FC = () => {
  const dispatch = useDispatch();
  const { t } = useI18n(); // 使用 i18n hook
  
  useEffect(() => {
    dispatch({
      type: ActionType.UpdateUserInfo,
      state: {
        userId: "Anonymous",
        displayName: "Anonymous",
        loginExpiration: 0,
        isLogin: true,
        username: "Anonymous",
      },
    });
  }, [dispatch]);

  return <App />;
};

export default AuthWithNothing;
