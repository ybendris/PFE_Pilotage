import { Component, OnInit } from '@angular/core';
import { Commande } from 'src/app/models/commande.model';
import { CommandService } from 'src/app/services/command.service';

@Component({
  selector: 'app-session',
  templateUrl: './session.component.html',
  styleUrls: ['./session.component.scss']
})
export class SessionComponent implements OnInit {
  commande: Commande
  constructor(public command_service: CommandService) { }
  ngOnInit(): void {
    //
  }
  sessionName = ''
  sessionDescription = ''

  create_session(){
    console.log("Session Name:" + this.sessionName)
    console.log("Description" + this.sessionDescription)
    this.commande = {
      destinataire: "DATA_COLLECT",
      msg: {"session" : this.sessionName, "description" : this.sessionDescription},
      params: [this.sessionName],
      action: "setNomSession"
    }
    
    this.command_service.sendCmd(this.commande, response => {
      this.command_service.router.navigate(['/IHM'], { state: { name: this.sessionName, description: this.sessionDescription } });
    });
    
  }

  

  /*
  Renvoie true si la variable sessionName est vide, et false sinon.
   */
  isNameEmpty(){
    return this.sessionName == '';
  }

  /*
  Renvoie true si la variable sessionDescription est vide, et false sinon.
   */
  isDescriptionEmpty() {
    return this.sessionDescription == '';
  }

  /*
  Utilise les fonctions isNameEmpty() et isDescriptionEmpty() pour vérifier si le composant est valide et renvoie true si les deux variables sont non vides, et false sinon.
   */

  isValid() {
    return !this.isNameEmpty() && !this.isDescriptionEmpty();
  }
}
