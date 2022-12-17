import { Component, OnInit } from '@angular/core';
import { CommandService } from '../../services/command.service'
import { Commande } from '../../models/commande.model';
import { Input } from '@angular/core';

@Component({
  selector: 'app-commande',
  templateUrl: './commande.component.html',
  styleUrls: ['./commande.component.scss']
})
export class CommandeComponent implements OnInit {
  commande: Commande
  @Input() sensor: string
  @Input() content: string
  @Input() sessionName: string

  constructor(public command_service: CommandService) { }

  ngOnInit(): void {
    //emit sessionName => send_command ?
  }

  /*
  sendCommand permet d'envoyer une commande au serveur Flask en utilisant la fonction sendCmd du service CommandService
  le destinataire et la commande sont des valeurs définis par des input html
   */
  sendCommand(){
    this.commande = {
      to: this.sensor,
      content: this.content
    }
    console.log(this.commande)
    this.command_service.sendCmd(this.commande)
  }

}
