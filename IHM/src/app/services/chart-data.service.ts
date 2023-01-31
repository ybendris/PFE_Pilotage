import { Injectable } from '@angular/core';
import {BehaviorSubject} from "rxjs";
import {Data} from "../models/data.model";

@Injectable({
  providedIn: 'root'
})
export class ChartDataService {

  /*
  Objet de type BehaviorSubject qui est utilisé pour stocker et diffuser des données.
  Un BehaviorSubject est un type de flux de données RxJS qui stocke la valeur actuelle et diffuse cette valeur à tous les abonnés lorsqu'ils s'abonnent.
  Dans ce cas, _data stocke une valeur de type Data qui est initialisée avec des valeurs par défauts.
   */
  private _data = new BehaviorSubject<Data<unknown>>({
    type: "",
    expediteur: "",
    paquet: "",
    msg: {}
  });
  /*
  Observable qui est créé à partir de _data en utilisant la méthode asObservable().
  Cela signifie que tous les abonnés à data$ recevront les valeurs diffusées par _data.
  */
  data$ = this._data.asObservable();

  constructor() { }

  //Met à jour et émet les nouvelles données au graphique
  updateData(data: Data<unknown>) {
    //console.log("updateData ", data)
    this._data.next(data);
  }

}
