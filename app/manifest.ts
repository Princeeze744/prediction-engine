import type {MetadataRoute} from 'next';
/* Lets phones and computers install the site as an app (home-screen icon, opens full screen without the browser bar). */
export default function manifest():MetadataRoute.Manifest{return {
 name:'QuantSport AI',short_name:'QuantSport',description:'Free football picks and ten mixed tickets every match day.',
 start_url:'/?source=app',scope:'/',display:'standalone',orientation:'portrait',background_color:'#04100c',theme_color:'#04100c',categories:['sports'],
 icons:[{src:'/icon-192.png',sizes:'192x192',type:'image/png'},{src:'/icon-512.png',sizes:'512x512',type:'image/png'},{src:'/icon-maskable.png',sizes:'512x512',type:'image/png',purpose:'maskable'}],
 shortcuts:[{name:'VIP tickets',url:'/tickets'},{name:'Free picks',url:'/picks'},{name:'No Draw',url:'/nodraw'}]}}
