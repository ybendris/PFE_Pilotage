import { Component } from '@angular/core';

@Component({
  selector: 'app-session',
  templateUrl: './session.component.html',
  styleUrls: ['./session.component.scss']
})
export class SessionComponent {
  sessionName = ''
  sessionDescription = ''

  create_session(){
    console.log("Session Name:" + this.sessionName)
    console.log("Description" + this.sessionDescription)
  }

  isNameEmpty(){
    if(this.sessionName == ""){
      return true
    }
    return false
  }

  isDescriptionEmpty(){
    if(this.sessionDescription == ""){
      return true
    }
    return false
  }

  isValid(){
    if (this.isNameEmpty() || this.isDescriptionEmpty()){
      return false
    }
    return true
  }



}
