'use client';
import {useEffect} from 'react';
export default function LegacyFilmLink(){
  useEffect(()=>{if(['casa','station','interior','courtyard','diner','alley'].includes(location.hash.slice(1)))location.replace('/film/'+location.search+location.hash);},[]);
  return null;
}
