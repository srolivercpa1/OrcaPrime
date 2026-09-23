"""Usuários locais. Não depende de serviço de licenças ou conexão externa."""
import base64
import hashlib
import hmac
import secrets
import time

ROLES = ('ADMIN', 'ATENDIMENTO', 'TECNICO', 'FINANCEIRO')


def encode_password(password):
    if not isinstance(password,str) or not 10 <= len(password) <= 256:
        raise ValueError('A senha deve ter entre 10 e 256 caracteres.')
    salt=secrets.token_bytes(16)
    return base64.b64encode(salt+hashlib.scrypt(password.encode(),salt=salt,n=16384,r=8,p=1)).decode()


def check_password(password,encoded):
    if not isinstance(password,str) or len(password)>256:return False
    try:
        raw=base64.b64decode(encoded,validate=True)
        return len(raw)==80 and hmac.compare_digest(raw[16:],hashlib.scrypt(password.encode(),salt=raw[:16],n=16384,r=8,p=1))
    except (ValueError,TypeError):return False


class Users:
    def __init__(self,store):
        self.store=store
        with store.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS app_users (
                id INTEGER PRIMARY KEY,username TEXT UNIQUE COLLATE NOCASE NOT NULL,
                name TEXT NOT NULL,role TEXT NOT NULL,password_hash TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,failures INTEGER NOT NULL DEFAULT 0,
                locked_until REAL NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS user_audit (
                id INTEGER PRIMARY KEY,at REAL NOT NULL,actor_id INTEGER NOT NULL,
                action TEXT NOT NULL,target_id INTEGER NOT NULL);
            ''')
    def has_users(self):
        with self.store.connect() as db:return bool(db.execute('SELECT 1 FROM app_users LIMIT 1').fetchone())
    def bootstrap(self,username,password):
        username=str(username).strip()
        if not username or len(username)>80:raise ValueError('Informe um usuário de até 80 caracteres.')
        hashed=encode_password(password)
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM app_users LIMIT 1').fetchone():raise ValueError('Administrador já configurado.')
            id_=db.execute('INSERT INTO app_users(username,name,role,password_hash) VALUES(?,?,?,?)',(username,username,'ADMIN',hashed)).lastrowid
            db.execute('INSERT INTO user_audit(at,actor_id,action,target_id) VALUES(?,?,?,?)',(time.time(),id_,'CONFIGURACAO_INICIAL',id_))
        return {'id':id_,'username':username,'name':username,'role':'ADMIN'}
    def authenticate(self,username,password):
        result=None
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT id,username,name,role,password_hash,active,failures,locked_until FROM app_users WHERE username=?',(str(username).strip(),)).fetchone()
            if row and row[5] and row[7]<=time.time():
                if check_password(password,row[4]):
                    db.execute('UPDATE app_users SET failures=0,locked_until=0 WHERE id=?',(row[0],))
                    result=dict(zip(('id','username','name','role'),row[:4]))
                    db.execute('INSERT INTO user_audit(at,actor_id,action,target_id) VALUES(?,?,?,?)',(time.time(),row[0],'LOGIN',row[0]))
                else:
                    failures=row[6]+1
                    db.execute('UPDATE app_users SET failures=?,locked_until=? WHERE id=?',(failures,time.time()+300 if failures>=5 else 0,row[0]))
        if result is None:raise ValueError('Usuário ou senha inválidos, conta desativada ou temporariamente bloqueada. Após cinco tentativas, aguarde cinco minutos.')
        return result
    def _admin(self,db,actor):
        row=db.execute('SELECT role,active FROM app_users WHERE id=?',(actor.get('id'),)).fetchone()
        if row!=('ADMIN',1):raise ValueError('Apenas administradores podem gerenciar usuários.')
    def list(self,actor):
        with self.store.connect() as db:
            self._admin(db,actor)
            return [dict(zip(('id','username','name','role','active'),r)) for r in db.execute('SELECT id,username,name,role,active FROM app_users ORDER BY username')]
    def save(self,actor,data,id_=None):
        username=str(data.get('username','')).strip();name=str(data.get('name',username)).strip()
        role=data.get('role');active=bool(data.get('active',True))
        if not username or len(username)>80 or not name or len(name)>120 or role not in ROLES:raise ValueError('Confira usuário, nome e perfil.')
        password=data.get('password','');hashed=encode_password(password) if password else None
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE');self._admin(db,actor)
            if db.execute('SELECT id FROM app_users WHERE username=? AND id!=?',(username,id_ or 0)).fetchone():raise ValueError('Usuário já cadastrado.')
            if id_:
                current=db.execute('SELECT role,active FROM app_users WHERE id=?',(id_,)).fetchone()
                if not current:raise ValueError('Usuário inexistente.')
                if id_==actor['id'] and (role!='ADMIN' or not active):raise ValueError('Não é possível remover o próprio acesso administrativo.')
                if current==('ADMIN',1) and (role!='ADMIN' or not active):
                    if db.execute("SELECT COUNT(*) FROM app_users WHERE role='ADMIN' AND active=1").fetchone()[0]<=1:raise ValueError('Mantenha ao menos um administrador ativo.')
                db.execute('UPDATE app_users SET username=?,name=?,role=?,active=? WHERE id=?',(username,name,role,int(active),id_))
                if hashed:db.execute('UPDATE app_users SET password_hash=?,failures=0,locked_until=0 WHERE id=?',(hashed,id_))
            else:
                if not hashed:raise ValueError('Informe a senha inicial.')
                id_=db.execute('INSERT INTO app_users(username,name,role,password_hash,active) VALUES(?,?,?,?,?)',(username,name,role,hashed,int(active))).lastrowid
            db.execute('INSERT INTO user_audit(at,actor_id,action,target_id) VALUES(?,?,?,?)',(time.time(),actor['id'],'ALTERAR_USUARIO',id_))
        return id_


def validate_users_database(db):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='app_users'").fetchone():return
    expected={'app_users':{'id','username','name','role','password_hash','active','failures','locked_until'},'user_audit':{'id','at','actor_id','action','target_id'}}
    for table,columns in expected.items():
        if db.execute('SELECT type FROM sqlite_master WHERE name=?',(table,)).fetchone()!=('table',):raise ValueError('Estrutura de usuários inválida.')
        if {r[1] for r in db.execute(f'PRAGMA table_info({table})')}!=columns:raise ValueError('Colunas de usuários inválidas.')
    rows=db.execute('SELECT id,username,name,role,password_hash,active,failures,locked_until FROM app_users').fetchall()
    if rows and not any(r[3]=='ADMIN' and r[5]==1 for r in rows):raise ValueError('Backup sem administrador ativo.')
    for r in rows:
        if r[3] not in ROLES or r[5] not in (0,1) or not r[1] or not r[2] or r[6]<0 or r[7]<0:raise ValueError('Usuário inválido no backup.')
        if len(base64.b64decode(r[4],validate=True))!=80:raise ValueError('Credencial inválida no backup.')
