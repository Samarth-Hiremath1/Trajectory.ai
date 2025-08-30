declare module 'ldrs/waveform' {
  const content: any;
  export default content;
}

declare module 'ldrs/react' {
  export interface WaveformProps {
    size?: string;
    stroke?: string;
    speed?: string;
    color?: string;
  }
  
  export const Waveform: React.FC<WaveformProps>;
}

declare global {
  namespace JSX {
    interface IntrinsicElements {
      'l-waveform': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
        size?: string;
        stroke?: string;
        speed?: string;
        color?: string;
      };
    }
  }
}