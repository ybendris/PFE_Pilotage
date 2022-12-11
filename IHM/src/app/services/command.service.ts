import { Injectable } from '@angular/core';
import {Socket} from "ngx-socket-io";
import {map} from "rxjs";
import { Commande } from '../models/commande.model';

@Injectable({
  providedIn: 'root'
})
export class CommandService {

  constructor(private socket: Socket) { }


  /*
  sendCmd utilise une propriété socket. Elle utilise la méthode emit pour envoyer un événement 'send_command' au serveur Flask, avec les données de la commande passée en argument.
   */

  sendCmd(commandeToSend : Commande){
    this.socket.emit('send_command', commandeToSend);
  }
}
