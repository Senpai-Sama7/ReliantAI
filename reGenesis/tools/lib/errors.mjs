export const ERROR_CODES = {
  PATH_TRAVERSAL: 'E_PATH_TRAVERSAL',
  FETCH_FAIL: 'E_FETCH_FAIL',
  MAX_SIZE: 'E_MAX_SIZE',
  ROBOTS_BLOCK: 'E_ROBOTS_BLOCK'
};

export class RegenesisError extends Error {
  constructor(code, message){
    super(message);
    this.code = code;
  }
}
