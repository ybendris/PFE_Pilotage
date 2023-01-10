import { Component, OnInit } from '@angular/core';
import { CommandService } from '../../services/command.service'
import { Commande } from '../../models/commande.model';
import { Input } from '@angular/core';
import { MatMenuModule } from '@angular/material/menu';

@Component({
  selector: 'app-commande',
  templateUrl: './commande.component.html',
  styleUrls: ['./commande.component.scss']
})
export class CommandeComponent implements OnInit {
  commande: Commande
  selectedService: string = ""
  selectedAction: string = ""
  data_Menu= {}
  actions: []
  @Input() sessionName: string

  constructor(public command_service: CommandService) {}

  ngOnInit(): void {
    this.rafraichir()
  }

  /*
  sendCommand permet d'envoyer une commande au serveur Flask en utilisant la fonction sendCmd du service CommandService
  le destinataire et la commande sont des valeurs définis par des input html
   */
  sendCommand(){
    if(this.isSendValid()){
      this.commande = {
        destinataire: this.selectedService,
        action: this.selectedAction,
        params: [""],
        msg: {}
      }
      console.log(this.commande)
      this.command_service.sendCmd(this.commande, this.print_response.bind(this))
    }
  }

  print_response(response){
    console.log(response)
  }

  rafraichir(){
    this.commande = {
      destinataire: "CENTRAL",
      action: "recup_action",
      params: [""],
      msg: {}
    }
    this.command_service.sendCmd(this.commande, this.acknowledge.bind(this))
  }

  acknowledge(response){
    this.data_Menu = response
  }

  updateActions() {
    console.log("updateActions")
    this.actions = this.data_Menu[this.selectedService];
  }



  isServiceEmpty(){
    return this.selectedService == '';
  }


  isActionEmpty() {
    return this.selectedAction == '';
  }



  isSendValid() {
    return !this.isServiceEmpty() && !this.isActionEmpty();
  }

}
