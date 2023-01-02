import { Injectable } from '@angular/core';
import {Socket} from "ngx-socket-io";
import { Commande } from '../models/commande.model';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})
export class CommandService {
  

  constructor(private socket: Socket, private router: Router) { }


  /*
  sendCmd utilise une propriété socket. Elle utilise la méthode emit pour envoyer un événement 'send_command' au serveur Flask, avec les données de la commande passée en argument.
   */

  sendCmd(commandeToSend : Commande){
    console.log("sendCmd " +commandeToSend)
    this.socket.emit('send_command', commandeToSend);
  }


  listenForResponse() {
    this.socket.fromEvent('response').subscribe((response:JSON) => {
      console.log('received response: ' + JSON.stringify(response));
      this.router.navigate(['/IHM'], { state: { name: 'My Session TODO', description: 'This is my session. TODO' } });
    });
  }
  

}
