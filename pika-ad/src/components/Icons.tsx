import {C} from '../theme';

type P = {size?: number; color?: string};

export const PinIcon: React.FC<P> = ({size = 48, color = C.black}) => (
  <svg width={size} height={size} viewBox="0 0 24 24">
    <path d="M12 2a7 7 0 0 0-7 7c0 5.2 7 13 7 13s7-7.8 7-13a7 7 0 0 0-7-7zm0 9.6A2.6 2.6 0 1 1 12 6.4a2.6 2.6 0 0 1 0 5.2z" fill={color} />
  </svg>
);

export const TruckIcon: React.FC<P> = ({size = 48, color = C.black}) => (
  <svg width={size} height={size} viewBox="0 0 24 24">
    <path d="M2 5h12v10H2zM14 9h4l3 3.5V15h-7z" fill={color} />
    <circle cx="6.5" cy="17.5" r="2.3" fill={color} />
    <circle cx="17" cy="17.5" r="2.3" fill={color} />
  </svg>
);

export const BagIcon: React.FC<P> = ({size = 48, color = C.black}) => (
  <svg width={size} height={size} viewBox="0 0 24 24">
    <path d="M5 7h14l-1.2 14H6.2z" fill={color} />
    <path d="M8.5 9V6.5a3.5 3.5 0 0 1 7 0V9" stroke={color} strokeWidth="2" fill="none" />
  </svg>
);

export const InstagramIcon: React.FC<P> = ({size = 48, color = C.cream}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2">
    <rect x="3" y="3" width="18" height="18" rx="5.5" />
    <circle cx="12" cy="12" r="4.2" />
    <circle cx="17.4" cy="6.6" r="1.1" fill={color} stroke="none" />
  </svg>
);

export const WhatsAppIcon: React.FC<P> = ({size = 48, color = C.cream}) => (
  <svg width={size} height={size} viewBox="0 0 24 24">
    <path
      d="M12 2.5a9.5 9.5 0 0 0-8.2 14.3L2.5 21.5l4.8-1.3A9.5 9.5 0 1 0 12 2.5zm0 2a7.5 7.5 0 1 1-3.9 13.9l-.3-.2-2.4.7.7-2.3-.2-.3A7.5 7.5 0 0 1 12 4.5zm-3 3.6c-.3 0-.7.1-1 .5-.3.4-1 1-1 2.4s1 2.8 1.2 3c.1.2 2 3.2 5 4.3 2.4.9 2.9.8 3.5.7.5-.1 1.7-.7 1.9-1.4.2-.7.2-1.3.2-1.4l-.5-.3-1.8-.9c-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.6.1a6.2 6.2 0 0 1-3-2.6c-.2-.4.2-.4.6-1.2.1-.2 0-.3 0-.5l-.8-2c-.2-.5-.4-.4-.6-.4z"
      fill={color}
    />
  </svg>
);
