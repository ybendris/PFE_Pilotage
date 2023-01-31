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
  le destinataire et la commande sont des valeurs définies par des input html
   */
  sendCommand(){
    if(this.isSendValid()){
      this.commande = {
        destinataire: this.selectedService,
        action: this.selectedAction,
        params: [""],
        msg: {}
      }
      //console.log(this.commande)
      this.command_service.sendCmd(this.commande, this.print_response.bind(this))
    }
  }

  print_response(response){
    //console.log(response)
  }

  /*
  Permet d’envoyer la commande “recup_action” au Central via le serveur Flask en utilisant la fonction sendCmd
  du service CommandService afin de récupérer et mettre à jour les services disponibles et leurs actions.
   */
  rafraichir(){
    this.commande = {
      destinataire: "CENTRAL",
      action: "recup_action",
      params: [""],
      msg: {}
    }
    this.command_service.sendCmd(this.commande, this.acknowledge.bind(this))
  }

  /*
  Récupére la réponse de la commande envoyer par la fonction rafraichir(), pour mettre à jour l’attribut data_Menu.
   */
  acknowledge(response){
    this.data_Menu = response
  }

  /*
  Permet de mettre à jour l’attribut actions avec les actions du service sélectionné
   */
  updateActions() {
    //console.log("updateActions")
    this.actions = this.data_Menu[this.selectedService];
  }

  /*
  Renvoie true si l’attribut selectedService est vide, false sinon
  */
  isServiceEmpty(){
    return this.selectedService == '';
  }


  /*
  Renvoie true si l’attribut selectedAction est vide, false sinon
   */
  isActionEmpty() {
    return this.selectedAction == '';
  }

  /*
  Utilise les fonctions isServiceEmpty() et isActionEmpty() pour vérifier si le le service et l’action sont valide
  renvoie true si les deux variables sont non vides, et false sinon.
   */
  isSendValid() {
    return !this.isServiceEmpty() && !this.isActionEmpty();
  }

}
