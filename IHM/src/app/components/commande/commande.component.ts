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

  constructor(public command_service: CommandService) { }

  ngOnInit(): void {
  }

  sendCommand(){

    this.commande = {
      to: this.sensor,
      content: this.content
    }
    console.log(this.commande)
    this.command_service.sendCmd(this.commande)
  }
}
