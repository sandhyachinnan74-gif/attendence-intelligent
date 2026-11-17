import React, { useState, useEffect } from 'react';

interface LiveClockProps {
  className?: string;
}

export const LiveClock: React.FC<LiveClockProps> = ({ className = 'text-2xl font-bold font-mono tracking-tight text-dark' }) => {
  const [time, setTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return <span className={className}>{time}</span>;
};
