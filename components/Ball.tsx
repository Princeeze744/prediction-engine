/* The football used by the opening screen and the loading states. */
export default function Ball({size=56}:{size?:number}){return <svg className="ball" width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
 <defs><radialGradient id="qsb" cx="38%" cy="32%" r="75%"><stop offset="0" stopColor="#ffffff"/><stop offset="1" stopColor="#c9d6cd"/></radialGradient></defs>
 <circle cx="32" cy="32" r="30" fill="url(#qsb)"/>
 <g fill="#07140f"><path d="M32 20l10.5 7.6-4 12.3h-13l-4-12.3z"/><path d="M32 2.2l8.6 3.4L32 11.5l-8.6-5.9z"/><path d="M60.5 23.5l1.3 9.1-7.6 5.6-3-9.9 4.9-7.2z"/><path d="M3.5 23.5l4.4-2.4 4.9 7.2-3 9.9-7.6-5.6z"/><path d="M48.6 56.7l-7.9 4.6-2.6-9.3 8.5-6 6.9 3.1z"/><path d="M15.4 56.7l-4.9-7.6 6.9-3.1 8.5 6-2.6 9.3z"/></g>
 <g stroke="#07140f" strokeWidth="1.6" fill="none"><path d="M32 11.5V20M42.5 27.6l8.7.7M38.5 39.9l8.1 6.1M25.5 39.9l-8.1 6.1M21.5 27.6l-8.7.7"/></g>
 <circle cx="32" cy="32" r="30" fill="none" stroke="rgba(0,0,0,.25)" strokeWidth="1"/></svg>}
export function Loader({label='Loading'}:{label?:string}){return <div className="loader" role="status"><span className="loader-ball"><Ball size={44}/></span><span className="loader-shadow"/><b>{label}</b></div>}
