export interface Data<T> {
  type: string,
  expediteur: string,
  paquet: string,
  msg: { [key: string]: T }
}
