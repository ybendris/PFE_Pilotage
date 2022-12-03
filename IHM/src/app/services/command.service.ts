import { Injectable } from '@angular/core';
import {Socket} from "ngx-socket-io";
import {map} from "rxjs";
import { Commande } from '../models/commande.model';

@Injectable({
  providedIn: 'root'
})
export class CommandService {

  constructor(private socket: Socket) { }


  sendCmd(commandeToSend : Commande){
    this.socket.emit('send_command', commandeToSend);
  }
}
