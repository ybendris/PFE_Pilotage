import { Injectable } from '@angular/core';
import {Socket} from "ngx-socket-io";
import { Commande } from '../models/commande.model';
import { Router } from '@angular/router';
import { take } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class CommandService {
  

  constructor(private socket: Socket, public router: Router) { }


  /*
  sendCmd utilise une propriété socket. Elle utilise la méthode emit pour envoyer un événement 'send_command' au serveur Flask, avec les données de la commande passée en argument.
   */

  sendCmd(command : Commande, callback){
    this.socket.emit('send_command', command);
    this.socket.fromEvent('response').pipe(take(1)).subscribe((response:JSON) => {
      console.log('received response: ' + JSON.stringify(response));
      callback(response);
    });
  }
  
}
