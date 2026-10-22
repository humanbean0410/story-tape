import WatchStory from '../../../components/watch-story';
export default async function WatchPage({params}:{params:Promise<{token:string}>}) {
  const {token}=await params;
  return <WatchStory token={token}/>;
}
