import { Octokit } from "octokit";
import { promises } from "fs";
import dotenv from 'dotenv';
import pkg from "base-64";

dotenv.config();
const { encode } = pkg;

const owner = "matthewplaisance";
const repo = "prod";
const gh_file = "data/allproductiondata.json";//file to update
const gh_file_cuml = "data/cumProd.json";//file to update


const raw = await promises.readFile("allproductiondata1.json", 'utf-8').then((data) => {return data;}).catch((error) => {console.log("err => ", error); return error;});
const rw = await promises.readFile("cumProd1.json", 'utf-8').then((data) => {return data;}).catch((error) => {console.log("err => ", error); return error;});

const contentProd = encode(raw);
const contentCuml = encode(rw)
const octokit = new Octokit({
    auth: process.env.TOKEN_MPPROD
})

async function putFile (ghFile, content) {
    const sha = await getSha(ghFile);
    octokit.request('PUT /repos/{owner}/{repo}/contents/{path}', {
        owner: owner,
        repo: repo,
        path: ghFile,
        message: 'update via api',
        committer: {
            name: 'matthew plaisance',
            email: 'mplaisance128@gmail.com'
        },
        content: content,
        sha: sha,
        headers: {
            'X-GitHub-Api-Version': '2022-11-28'
        }
    })
    .then((response) => {
        const data = response.data
    })
    .catch((err) => {
        console.log('err :>> ', err);
    })
}

async function getSha (ghFile) {
    return octokit.request("GET /repos/{owner}/{repo}/contents/{path}", {
        owner,
        repo,
        path: ghFile,
      })
        .then((response) => {
          const fileData = response.data;
          const blobSha = fileData.sha;
      
          return blobSha;
        })
        .catch((error) => {
          console.error("Error retrieving blob SHA:", error);
          return null;
        });
}

putFile(gh_file,contentProd);
putFile(gh_file_cuml,contentCuml);
