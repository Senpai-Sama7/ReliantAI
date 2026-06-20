import { MOTION, PREMIUM_EASE } from "./design-quality-standards";

/** Framer-motion transition using premium easing — never ease-in-out */
export const premiumTransition = (delay = 0, duration: number = MOTION.duration.base) => ({
  duration,
  delay,
  ease: PREMIUM_EASE,
});

export const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
};
