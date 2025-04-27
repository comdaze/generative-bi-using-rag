import { TopNavigation } from "@cloudscape-design/components";
// import { Mode } from '@cloudscape-design/global-styles'
import { useMsal } from "@azure/msal-react";
import { Density } from "@cloudscape-design/global-styles";
import { Auth } from "aws-amplify";
import { useEffect, useState } from "react";
import { useAuth } from "react-oidc-context";
import { useSelector } from "react-redux";
import {
  APP_LOGO,
  APP_RIGHT_LOGO,
  APP_TITLE,
  APP_VERSION,
  AUTH_WITH_AZUREAD,
  AUTH_WITH_COGNITO,
  AUTH_WITH_OIDC,
  AUTH_WITH_SSO,
  CHATBOT_NAME,
} from "../../utils/constants";
import { Storage } from "../../utils/helpers/storage";
import { UserState } from "../../utils/helpers/types";
import { useI18n } from "../../utils/i18n";
import "./style.scss";

export default function TopNav() {
  // const [theme, setTheme] = useState<Mode>(Storage.getTheme())
  const userInfo = useSelector((state: UserState) => state.userInfo);
  const { language, setLanguage, t } = useI18n();
  const [, forceUpdate] = useState({});

  const [isCompact, setIsCompact] = useState<boolean>(
    Storage.getDensity() === Density.Compact
  );
  const { instance } = useMsal();
  const auth = useAuth();

  // Force re-render when language changes
  useEffect(() => {
    const handleLanguageChange = () => {
      forceUpdate({});
    };
    
    window.addEventListener('languageChanged', handleLanguageChange);
    return () => {
      window.removeEventListener('languageChanged', handleLanguageChange);
    };
  }, []);

  // const onChangeThemeClick = () => {
  //   if (theme === Mode.Dark) {
  //     setTheme(Storage.applyTheme(Mode.Light))
  //   } else {
  //     setTheme(Storage.applyTheme(Mode.Dark))
  //   }
  // }

  const toggleLanguage = () => {
    const newLang = language === 'en' ? 'zh' : 'en';
    setLanguage(newLang);
    console.log("Language changed to:", newLang);
  };

  return (
    <div
      style={{ zIndex: 1002, top: 0, left: 0, right: 0, position: "fixed" }}
      id="awsui-top-navigation"
    >
      {APP_RIGHT_LOGO && (
        <img className="logo" src={APP_RIGHT_LOGO} alt="logo" />
      )}
      <TopNavigation
        identity={{
          href: "/",
          title: `${APP_TITLE} ${APP_VERSION}`,
          logo: APP_LOGO
            ? {
                src: APP_LOGO,
                alt: { CHATBOT_NAME } + " Logo",
              }
            : undefined,
        }}
        utilities={[
          // {
          //   type: 'button',
          //   text: theme === Mode.Dark ? 'Light Mode' : 'Dark Mode',
          //   onClick: onChangeThemeClick,
          // },
          {
            type: "button",
            iconName: isCompact ? "view-full" : "zoom-to-fit",
            text: isCompact ? t('common.compact') : t('common.comfortable'),
            ariaLabel: "SpacingSwitch",
            onClick: () => {
              setIsCompact((prev) => {
                Storage.applyDensity(
                  !prev ? Density.Compact : Density.Comfortable
                );
                return !prev;
              });
            },
          },
          {
            type: "button",
            iconName: "globe",
            text: language === 'en' ? t('topNav.switchToChinese') : t('topNav.switchToEnglish'),
            ariaLabel: "LanguageSwitch",
            onClick: toggleLanguage,
          },
          {
            type: "menu-dropdown",
            text: userInfo?.displayName || "Authenticating",
            // description: `username: ${userInfo?.username}`,
            iconName: "user-profile",
            onItemClick: ({ detail }) => {
              if (detail.id === "signout") {
                if (AUTH_WITH_COGNITO || AUTH_WITH_SSO) {
                  Auth.signOut();
                }
                if (AUTH_WITH_OIDC) {
                  auth.signoutSilent();
                }
                if (AUTH_WITH_AZUREAD) {
                  instance.logoutRedirect({
                    postLogoutRedirectUri: "/",
                  });
                }
              }
            },
            items: [
              {
                itemType: "group",
                id: "user-info",
                text: t('common.userInfo'),
                items: [
                  {
                    id: "0",
                    text: `${t('common.username')}: ${userInfo?.username}`,
                  },
                  {
                    id: "1",
                    text: `${t('common.userId')}: ${userInfo?.userId}`,
                  },
                  {
                    id: "2",
                    text: `${t('common.loginExpiration')}: ${userInfo?.loginExpiration}`,
                    disabled: true,
                  },
                ],
              },
              {
                id: "signout",
                text: t('common.signOut'),
              },
            ],
          },
        ]}
      />
    </div>
  );
}
