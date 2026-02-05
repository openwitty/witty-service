import { NavLink } from "react-router";
import { useTranslation } from "react-i18next";
import HomeIcon from "#/assets/branding/home-icon.svg?react";
import { I18nKey } from "#/i18n/declaration";
import { StyledTooltip } from "#/components/shared/buttons/styled-tooltip";

export function OpenHandsLogoButton() {
  const { t } = useTranslation();

  const tooltipText = t(I18nKey.BRANDING$HOME);
  const ariaLabel = t(I18nKey.BRANDING$HOME_BUTTON);

  return (
    <StyledTooltip content={tooltipText}>
      <NavLink to="/" aria-label={ariaLabel}>
        <HomeIcon width={46} height={30} />
      </NavLink>
    </StyledTooltip>
  );
}
