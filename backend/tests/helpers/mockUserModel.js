// backend/tests/helpers/mockUserModel.js
// NEW FILE
//
// Mocks User.create/findOne/findById/findByIdAndUpdate against an
// in-memory Map, so the auth/profile route tests can run without a
// live MongoDB connection.
//
// If your environment can reach fastdl.mongodb.org, swap this out
// for mongodb-memory-server + a real mongoose.connect() in
// beforeAll/afterAll instead — the route/controller code under test
// doesn't change either way, only how User's static methods are
// backed. This mock exists purely because that binary download was
// blocked in the sandbox this suite was authored in.

const { User } = require('../../src/modules/users');

function installUserModelMock() {
  const store = new Map();
  let idCounter = 1;

  function makeDoc(fields) {
    const _id = String(idCounter++);
    const doc = {
      _id,
      ...fields,
      toJSON() {
        const { passwordHash, __v, ...rest } = this;
        return { ...rest, _id: this._id };
      },
    };
    store.set(_id, doc);
    return doc;
  }

  User.create = async (fields) => {
    const existing = [...store.values()].find((d) => d.email === fields.email);
    if (existing) {
      const err = new Error('E11000 duplicate key');
      err.code = 11000;
      throw err;
    }
    return makeDoc({ ...fields, refreshTokenVersion: fields.refreshTokenVersion ?? 0 });
  };

  User.findOne = (query) => ({
    select: async () => {
      const email = query.email;
      return [...store.values()].find((d) => d.email === email) || null;
    },
  });

  User.findById = async (id) => store.get(String(id)) || null;

  User.findByIdAndUpdate = async (id, update, _opts) => {
    const doc = store.get(String(id));
    if (!doc) return null;
    if (update.$inc) {
      for (const [key, delta] of Object.entries(update.$inc)) {
        doc[key] = (doc[key] || 0) + delta;
      }
    } else {
      Object.assign(doc, update);
    }
    return doc;
  };

  return store;
}

module.exports = { installUserModelMock };