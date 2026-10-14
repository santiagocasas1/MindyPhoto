import {Composition} from 'remotion';
import {PikaAd} from './PikaAd';
import {FPS, DURATION} from './timeline';
import './fonts';

export const Root: React.FC = () => (
  <Composition id="PikaAd" component={PikaAd} durationInFrames={DURATION} fps={FPS} width={1080} height={1920} />
);
