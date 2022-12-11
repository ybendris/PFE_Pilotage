import { Injectable } from '@angular/core';
import {Socket} from "ngx-socket-io";
import {map} from "rxjs";

@Injectable({
  providedIn: 'root'
})
export class SocketService {


  constructor(private socket: Socket) {
  }

  /*
  Ces fonctions utilisent une propriété socket. Elle utilise la méthode 'fromEvent' pour souscrire à un événement 'get_data' ou 'get_log' émis par le serveur Flask.
  On utilise ensuite map pour transformer les données reçues en un format utilisable.
  Les fonctions renvoient un objet de type Observable, qui peut être utilisé pour s'abonner aux données envoyées par le serveur Flask lorsque l'événement 'get_data' ou 'get_log' est émis.
  */

  getData(){
    return this.socket.fromEvent("get_data").pipe(map((data:any) => data))
  }

  getLog(){
    return this.socket.fromEvent("get_log").pipe(map((log:any) => log))
  }




}
